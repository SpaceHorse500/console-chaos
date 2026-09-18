from __future__ import annotations

import os
import re
import shlex


ALIASES = {
    "gawk": "awk",
    "mawk": "awk",
    "nawk": "awk",
    "egrep": "grep",
    "fgrep": "grep",
}


def canonical_tool(name: str) -> str:
    base = os.path.basename(name)
    return ALIASES.get(base, base)


def _tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|&;()<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return []


def extract_executables(command: str) -> list[str]:
    """Best-effort executable extraction for pedagogical focused-mode checks.

    This is intentionally not a security boundary. The Docker sandbox is the
    security boundary; this parser only enforces learning rules in the grader.
    """
    tokens = _tokens(command)
    if not tokens:
        return []

    separators = {"|", "||", "&&", ";", "(", ")"}
    redirections = {"<", ">", ">>", "<<", "<<<", "<>"}
    result: list[str] = []
    expect_command = True
    skip_redir_target = False

    for token in tokens:
        if token in separators:
            expect_command = True
            skip_redir_target = False
            continue

        if token in redirections or re.fullmatch(r"\d*(?:>|>>|<|<<|<<<|<>)", token):
            skip_redir_target = True
            continue

        if skip_redir_target:
            skip_redir_target = False
            continue

        if not expect_command:
            continue

        # Environment assignments can precede a command.
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", token):
            continue

        # Numeric file-descriptor fragments are not executables.
        if token.isdigit():
            continue

        tool = canonical_tool(token)
        result.append(tool)
        expect_command = False

    return result


def validate_allowed_tools(command: str, allowed_tools: list[str]) -> dict:
    detected = extract_executables(command)
    allowed = {canonical_tool(tool) for tool in allowed_tools}
    forbidden = sorted({tool for tool in detected if tool not in allowed})
    return {
        "detected_tools": detected,
        "allowed_tools": sorted(allowed),
        "forbidden_tools": forbidden,
        "ok": not forbidden,
    }


def _has_executable(command: str, tool: str) -> bool:
    return canonical_tool(tool) in extract_executables(command)


def detect_command_skills(command: str) -> set[str]:
    """Infer concepts visibly demonstrated by a submitted shell command.

    The goal is conservative educational evidence, not perfect shell parsing.
    Unknown/clever solutions still grade by stdout; they simply do not receive
    concept credit that we cannot confidently identify.
    """
    found: set[str] = set()

    # Shell composition. Use tokenized shell punctuation where possible so
    # operators inside quoted awk/sed/jq programs are not misclassified.
    tokens = _tokens(command)
    pipe_count = tokens.count("|") if tokens else len(re.findall(r"(?<!\|)\|(?!\|)", command))
    if pipe_count >= 1:
        found.add("shell.pipeline.basic")
    if pipe_count >= 2:
        found.add("shell.pipeline.multi")
    if re.search(r"(^|\s)<\s*\S+", command):
        found.add("shell.redirection.input")
    if ">" in tokens:
        found.add("shell.redirection.output")
    if ">>" in tokens:
        found.add("shell.redirection.append")
        found.add("shell.redirection.output")
    if re.search(r"(?:^|\s)2\s*>\s*\S+", command) or re.search(r"(?:^|\s)2>\S+", command):
        found.add("shell.redirection.stderr")
    if "&&" in tokens:
        found.add("shell.boolean.and")
    if "||" in tokens:
        found.add("shell.boolean.or")
    if ";" in tokens:
        found.add("shell.sequence")
    if "(" in tokens and ")" in tokens:
        found.add("shell.subshell")

    # AWK.
    if _has_executable(command, "awk"):
        if re.search(r"\$(?:0|[1-9][0-9]*)\b", command) or re.search(r"\bprint\b", command):
            found.add("awk.fields")
        if re.search(r"(?:^|\s)-F(?:\s|\S)", command):
            found.add("awk.separator")
        if re.search(r"(?:==|!=|>=|<=|&&|\|\||(?<![<>])>(?!=)|(?<![<>])<(?!=))", command):
            found.add("awk.conditions")
        if re.search(r"\b(?:NR|NF)\b", command):
            found.add("awk.nr_nf")
        if (
            re.search(r"\b(?:awk|gawk|mawk|nawk)\b[^|;]*[\"']/(?:\\/|[^/])+/", command)
            or re.search(r"(?:!~|(?<!!)~)", command)
        ):
            found.add("awk.regex")

        has_end = bool(re.search(r"\bEND\b", command))
        has_state_update = bool(
            re.search(r"\b[A-Za-z_]\w*\s*(?:\+\+|--|\+=|-=|\*=|/=)", command)
            or re.search(r"\b[A-Za-z_]\w*\s*=\s*[^=]", command)
        )
        if has_end and has_state_update:
            found.add("awk.variables_end")

        if re.search(r"\b(?:for|while)\s*\(", command):
            found.add("awk.loops")
        if re.search(r"\$[A-Za-z_]\w*\b|\$\([^)]*[A-Za-z_][^)]*\)", command):
            found.add("awk.dynamic_fields")
        if re.search(r"\bsplit\s*\(", command):
            found.add("awk.split")
        if re.search(r"\b(?:g?sub)\s*\(", command):
            found.add("awk.substitution")

        has_array = bool(re.search(r"\b[A-Za-z_]\w*\s*\[[^\]]+\]", command))
        if has_array:
            found.add("awk.assoc_arrays")
        if has_array and has_end and re.search(r"\bfor\s*\(", command):
            found.add("awk.aggregation")

    # grep.
    if _has_executable(command, "grep"):
        found.add("grep.literal")
        grep_parts = [part for part in re.split(r"(?<!\|)\|(?!\|)|&&|;", command) if re.search(r"\b(?:grep|egrep|fgrep)\b", part)]
        grep_text = " ".join(grep_parts)
        if re.search(r"(?:^|\s)-[^\s]*v", grep_text):
            found.add("grep.invert")
        if re.search(r"(?:^|\s)-[^\s]*i", grep_text):
            found.add("grep.ignore_case")
        if re.search(r"(?:^|\s)-[^\s]*F", grep_text) or re.search(r"\bfgrep\b", grep_text):
            found.add("grep.fixed")
        if re.search(r"(?:^|\s)-[^\s]*w", grep_text):
            found.add("grep.word")
        if re.search(r"(?:^|\s)-[^\s]*c", grep_text):
            found.add("grep.count")
        if re.search(r"(?:^|\s)-[^\s]*n", grep_text):
            found.add("grep.line_numbers")
        if len(re.findall(r"(?:^|\s)-e(?:\s|$)", grep_text)) >= 2:
            found.add("grep.multiple_patterns")
        if re.search(r"(?:^|\s)-(?:A|B|C)(?:\s*\d+|\d+)", grep_text):
            found.add("grep.context")
        if re.search(r"(?:^|\s)-[^\s]*[rR]", grep_text):
            found.add("grep.recursive")
        if re.search(r"(?:^|\s)-[^\s]*E", grep_text) or re.search(r"\begrep\b", grep_text):
            found.add("grep.extended")
            found.add("grep.regex")
        elif "grep.fixed" not in found and re.search(r"[\^$\[\].*+?()|]", grep_text):
            found.add("grep.regex")

    # sort.
    if _has_executable(command, "sort"):
        found.add("sort.basic")
        sort_parts = [part for part in re.split(r"(?<!\|)\|(?!\|)|&&|;", command) if re.search(r"\bsort\b", part)]
        sort_text = " ".join(sort_parts)
        if re.search(r"(?:^|\s)-[^\s]*u", sort_text):
            found.add("sort.unique")
        if re.search(r"(?:^|\s)-[^\s]*[nr]", sort_text) or re.search(r"-k\S*[nr]\b", sort_text):
            found.add("sort.numeric_reverse")
        key_count = len(re.findall(r"(?:^|\s)-k", sort_text))
        if key_count >= 1:
            found.add("sort.keys")
        if key_count >= 2:
            found.add("sort.multiple_keys")
        if re.search(r"(?:^|\s)-t(?:\s*\S|\S)", sort_text):
            found.add("sort.delimiter")
        if re.search(r"(?:^|\s)-[^\s]*h", sort_text):
            found.add("sort.human")
        if re.search(r"(?:^|\s)-[^\s]*V", sort_text):
            found.add("sort.version")
        if re.search(r"(?:^|\s)-[^\s]*M", sort_text):
            found.add("sort.month")
        if re.search(r"(?:^|\s)-[^\s]*s", sort_text):
            found.add("sort.stable")

    if _has_executable(command, "uniq"):
        found.add("uniq.basic")
        if re.search(r"\buniq\s+[^|;]*-[^\s]*c", command):
            found.add("uniq.count")
        if re.search(r"\buniq\s+[^|;]*-[^\s]*d", command):
            found.add("uniq.duplicates_only")
        if re.search(r"\buniq\s+[^|;]*-[^\s]*u", command):
            found.add("uniq.unique_only")
        if re.search(r"\buniq\s+[^|;]*-[^\s]*i", command):
            found.add("uniq.ignore_case")
        if re.search(r"\buniq\s+[^|;]*(?:-f\s*\d+|--skip-fields(?:=|\s)\d+)", command):
            found.add("uniq.skip_fields")

    if _has_executable(command, "wc"):
        wc_flags = set()
        if re.search(r"\bwc\s+[^|;]*-[^\s]*l", command):
            found.add("wc.lines"); wc_flags.add("l")
        if re.search(r"\bwc\s+[^|;]*-[^\s]*w", command):
            found.add("wc.words"); wc_flags.add("w")
        if re.search(r"\bwc\s+[^|;]*-[^\s]*c", command):
            found.add("wc.bytes"); wc_flags.add("c")
        if re.search(r"\bwc\s+[^|;]*-[^\s]*m", command):
            found.add("wc.chars"); wc_flags.add("m")
        if len(wc_flags) >= 2:
            found.add("wc.multiple")

    if _has_executable(command, "sed"):
        sed_text = " ".join(part for part in re.split(r"(?<!\|)\|(?!\|)|&&|;", command) if re.search(r"\bsed\b", part))
        if re.search(r"\bsed\b[^|;]*\bs.", command):
            found.add("sed.substitute")
        if re.search(r"\bsed\b[^|;]*s(.).+\1.+\1g", command):
            found.add("sed.global")
        if re.search(r"""(?:['"])(?:\d+|/[^/]+/)(?:,)?""", sed_text):
            found.add("sed.address")
        if re.search(r"""(?:['"])(?:\d+|/[^/]+/),(?:\d+|/[^/]+/)""", sed_text):
            found.add("sed.range")
            found.add("sed.address")
        if re.search(r"""(?:['"]).*(?:^|[^A-Za-z])d(?:[;'"]|$)""", sed_text):
            found.add("sed.delete")
        if re.search(r"\bsed\s+[^|;]*-n", sed_text) and re.search(r"""(?:^|[^A-Za-z])p(?:[;'"]|$)""", sed_text):
            found.add("sed.print_only")
        if re.search(r"\\[1-9]", sed_text):
            found.add("sed.backrefs")
        if len(re.findall(r"(?:^|\s)-e(?:\s|$)", sed_text)) >= 2:
            found.add("sed.multiple_expr")
        if re.search(r"""(?:['"]).*(?:^|[^A-Za-z])[iac]\\""", sed_text):
            found.add("sed.iac")

    if _has_executable(command, "find"):
        if "-name" in command or "-type" in command:
            found.add("find.name_type")
        if "-size" in command:
            found.add("find.size")
        if "-maxdepth" in command or "-mindepth" in command:
            found.add("find.depth")
        if " -o " in command or " -not " in command or " ! " in command:
            found.add("find.logic")
        if "-exec" in command:
            found.add("find.exec")
        if "-path" in command:
            found.add("find.path")

    if _has_executable(command, "jq"):
        if re.search(r"\.[A-Za-z_][A-Za-z0-9_]*", command):
            found.add("jq.field")
        if re.search(r"\bjq\s+[^|;]*-[^\s]*r", command):
            found.add("jq.raw")
        if "select(" in command:
            found.add("jq.select")
        if re.search(r"\b(?:and|or|not)\b", command):
            found.add("jq.boolean")
        if re.search(r"\[[^]]*\.[A-Za-z_][^]]*,[^]]*\.[A-Za-z_]", command):
            found.add("jq.multi_field")
            found.add("jq.arrays")
        if re.search(r"\.[A-Za-z_][A-Za-z0-9_]*\s*\[\s*\d+\s*\]", command) or re.search(r"\[[^]]*\]", command):
            found.add("jq.arrays")
        if re.search(r"\blength\b", command):
            found.add("jq.length")
        if "map(" in command:
            found.add("jq.map")
            found.add("jq.arrays")
        if "sort_by(" in command:
            found.add("jq.sort_by")
            found.add("jq.arrays")
        if "group_by(" in command:
            found.add("jq.group_by")
            found.add("jq.arrays")
        if "unique_by(" in command:
            found.add("jq.unique_by")
            found.add("jq.arrays")
        if "min_by(" in command or "max_by(" in command:
            found.add("jq.minmax")
            found.add("jq.arrays")
        if re.search(r"\.[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", command):
            found.add("jq.nested")
        if re.search(r"\{\s*[A-Za-z_][A-Za-z0-9_]*\s*:", command):
            found.add("jq.construct")

    if _has_executable(command, "head"):
        found.add("head.basic")
        if re.search(r"\bhead\s+[^|;]*-[^\s]*c", command):
            found.add("head.bytes")
    if _has_executable(command, "tail"):
        found.add("tail.basic")
        if re.search(r"\btail\s+[^|;]*-n\s*\+\d+", command):
            found.add("tail.from_line")
        if re.search(r"\btail\s+[^|;]*-[^\s]*c", command):
            found.add("tail.bytes")
    if _has_executable(command, "cut"):
        if re.search(r"\bcut\s+[^|;]*-[^\s]*c", command):
            found.add("cut.characters")
        else:
            found.add("cut.fields")
        if re.search(r"(?:-f|--fields(?:=|\s))\s*\d+(?:,\d+)+", command):
            found.add("cut.multiple_fields")
        if re.search(r"(?:-f|--fields(?:=|\s))\s*\d+\s*-\s*\d+", command):
            found.add("cut.range")
        if "--complement" in command:
            found.add("cut.complement")

    return found
