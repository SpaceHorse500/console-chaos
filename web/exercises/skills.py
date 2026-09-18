from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
import re

from .command_analysis import detect_command_skills


@dataclass(frozen=True)
class SkillDefinition:
    id: str
    tool: str
    name: str
    level: int
    requires: tuple[str, ...] = ()
    description: str = ""


# The curriculum is intentionally small and explicit. Add skills here first,
# then reference their IDs from exercise templates.
SKILLS: dict[str, SkillDefinition] = {
    # shell / pipelines
    "shell.pipeline.basic": SkillDefinition(
        "shell.pipeline.basic", "shell", "Two-command pipelines", 1,
        description="Pass stdout from one command into another with |.",
    ),
    "shell.pipeline.multi": SkillDefinition(
        "shell.pipeline.multi", "shell", "Multi-stage pipelines", 2,
        ("shell.pipeline.basic",),
        "Build pipelines with three or more transformations.",
    ),
    "shell.redirection.input": SkillDefinition(
        "shell.redirection.input", "shell", "Input redirection", 1,
        description="Feed a file to stdin with <.",
    ),
    "shell.redirection.output": SkillDefinition(
        "shell.redirection.output", "shell", "Output redirection (>)", 2,
        description="Write stdout to a file, replacing its contents.",
    ),
    "shell.redirection.append": SkillDefinition(
        "shell.redirection.append", "shell", "Append redirection (>>)", 2,
        ("shell.redirection.output",),
        "Append stdout to a file without replacing existing contents.",
    ),
    "shell.redirection.stderr": SkillDefinition(
        "shell.redirection.stderr", "shell", "stderr redirection (2>)", 3,
        description="Redirect standard error separately from standard output.",
    ),
    "shell.boolean.and": SkillDefinition(
        "shell.boolean.and", "shell", "Conditional AND (&&)", 2,
        description="Run the next command only when the previous command succeeds.",
    ),
    "shell.boolean.or": SkillDefinition(
        "shell.boolean.or", "shell", "Conditional OR (||)", 2,
        description="Run the next command only when the previous command fails.",
    ),
    "shell.sequence": SkillDefinition(
        "shell.sequence", "shell", "Command sequencing (;)", 2,
        description="Run commands sequentially regardless of the previous exit status.",
    ),
    "shell.subshell": SkillDefinition(
        "shell.subshell", "shell", "Subshell grouping", 3,
        ("shell.sequence",),
        "Group commands with parentheses so their combined output can be redirected or piped.",
    ),

    # awk
    "awk.fields": SkillDefinition(
        "awk.fields", "awk", "Fields & print", 1,
        description="Use $0, $1, $2… and print.",
    ),
    "awk.separator": SkillDefinition(
        "awk.separator", "awk", "Field separator (-F)", 1,
        ("awk.fields",),
        "Change how awk splits each input row.",
    ),
    "awk.conditions": SkillDefinition(
        "awk.conditions", "awk", "Conditions", 2,
        ("awk.fields",),
        "Filter rows using comparisons and boolean operators.",
    ),
    "awk.nr_nf": SkillDefinition(
        "awk.nr_nf", "awk", "NR / NF", 2,
        ("awk.fields",),
        "Use the current row number and number of fields.",
    ),
    "awk.regex": SkillDefinition(
        "awk.regex", "awk", "Regex matching", 3,
        ("awk.fields",),
        "Use /regex/, ~ and !~ to select text.",
    ),
    "awk.variables_end": SkillDefinition(
        "awk.variables_end", "awk", "Variables, counters & END", 4,
        ("awk.conditions",),
        "Accumulate state while reading and report it in END.",
    ),
    "awk.loops": SkillDefinition(
        "awk.loops", "awk", "for loops", 5,
        ("awk.nr_nf",),
        "Iterate through fields or collections.",
    ),
    "awk.dynamic_fields": SkillDefinition(
        "awk.dynamic_fields", "awk", "Dynamic fields", 5,
        ("awk.loops", "awk.nr_nf"),
        "Use $i or $(i+1) when the field position is discovered at runtime.",
    ),
    "awk.split": SkillDefinition(
        "awk.split", "awk", "split()", 6,
        ("awk.loops",),
        "Split a field into parts inside awk.",
    ),
    "awk.substitution": SkillDefinition(
        "awk.substitution", "awk", "sub() / gsub()", 6,
        ("awk.conditions",),
        "Modify text inside awk before comparing or printing it.",
    ),
    "awk.assoc_arrays": SkillDefinition(
        "awk.assoc_arrays", "awk", "Associative arrays", 7,
        ("awk.variables_end", "awk.loops"),
        "Index counters or values by strings such as IPs or services.",
    ),
    "awk.aggregation": SkillDefinition(
        "awk.aggregation", "awk", "Aggregation in AWK", 8,
        ("awk.assoc_arrays", "awk.variables_end"),
        "Group and summarize data without relying on sort/uniq.",
    ),

    # grep
    "grep.literal": SkillDefinition(
        "grep.literal", "grep", "Literal matching", 1,
        description="Print lines containing a text pattern.",
    ),
    "grep.invert": SkillDefinition(
        "grep.invert", "grep", "Invert matches (-v)", 2,
        ("grep.literal",),
        "Keep lines that do not match.",
    ),
    "grep.regex": SkillDefinition(
        "grep.regex", "grep", "Regex patterns", 3,
        ("grep.literal",),
        "Use anchors, character classes and regex structure.",
    ),
    "grep.extended": SkillDefinition(
        "grep.extended", "grep", "Extended regex (-E)", 4,
        ("grep.regex",),
        "Use alternation and richer regular expressions.",
    ),
    "grep.ignore_case": SkillDefinition(
        "grep.ignore_case", "grep", "Case-insensitive matching (-i)", 2,
        ("grep.literal",),
        "Match text without treating uppercase and lowercase as different.",
    ),
    "grep.fixed": SkillDefinition(
        "grep.fixed", "grep", "Fixed strings (-F)", 2,
        ("grep.literal",),
        "Treat the search pattern literally instead of as a regular expression.",
    ),
    "grep.word": SkillDefinition(
        "grep.word", "grep", "Whole-word matching (-w)", 2,
        ("grep.literal",),
        "Match a word only at word boundaries.",
    ),
    "grep.count": SkillDefinition(
        "grep.count", "grep", "Count matches (-c)", 2,
        ("grep.literal",),
        "Print the number of matching lines instead of the lines themselves.",
    ),
    "grep.line_numbers": SkillDefinition(
        "grep.line_numbers", "grep", "Line numbers (-n)", 2,
        ("grep.literal",),
        "Prefix matching lines with their input line number.",
    ),
    "grep.multiple_patterns": SkillDefinition(
        "grep.multiple_patterns", "grep", "Multiple patterns (-e)", 3,
        ("grep.literal",),
        "Match any of several independent patterns in one grep command.",
    ),
    "grep.context": SkillDefinition(
        "grep.context", "grep", "Context lines (-A/-B/-C)", 3,
        ("grep.literal",),
        "Include lines before or after each match for surrounding context.",
    ),
    "grep.recursive": SkillDefinition(
        "grep.recursive", "grep", "Recursive search (-r/-R)", 3,
        ("grep.literal",),
        "Search files recursively below a directory.",
    ),

    # sort
    "sort.basic": SkillDefinition(
        "sort.basic", "sort", "Basic sorting", 1,
        description="Sort lines using normal text order.",
    ),
    "sort.unique": SkillDefinition(
        "sort.unique", "sort", "Unique sorting (-u)", 2,
        ("sort.basic",),
        "Sort and remove duplicate lines in one step.",
    ),
    "sort.numeric_reverse": SkillDefinition(
        "sort.numeric_reverse", "sort", "Numeric / reverse sorting", 3,
        ("sort.basic",),
        "Sort values numerically and/or in reverse order.",
    ),
    "sort.keys": SkillDefinition(
        "sort.keys", "sort", "Sort keys (-k)", 4,
        ("sort.basic",),
        "Sort using a selected field rather than the whole line.",
    ),
    "sort.multiple_keys": SkillDefinition(
        "sort.multiple_keys", "sort", "Multiple sort keys", 5,
        ("sort.keys", "sort.numeric_reverse"),
        "Use primary and tie-breaker sort keys.",
    ),
    "sort.delimiter": SkillDefinition(
        "sort.delimiter", "sort", "Field delimiter (-t)", 4,
        ("sort.keys",),
        "Choose a delimiter so sort keys line up with delimited columns.",
    ),
    "sort.human": SkillDefinition(
        "sort.human", "sort", "Human-readable numbers (-h)", 3,
        ("sort.basic",),
        "Sort values such as 900K, 12M and 2G by their numeric magnitude.",
    ),
    "sort.version": SkillDefinition(
        "sort.version", "sort", "Version sorting (-V)", 3,
        ("sort.basic",),
        "Sort strings containing version-like numeric components naturally.",
    ),
    "sort.month": SkillDefinition(
        "sort.month", "sort", "Month sorting (-M)", 3,
        ("sort.basic",),
        "Sort leading month names in calendar order.",
    ),
    "sort.stable": SkillDefinition(
        "sort.stable", "sort", "Stable sorting (-s)", 4,
        ("sort.keys",),
        "Preserve original input order when selected sort keys compare equal.",
    ),

    # uniq
    "uniq.basic": SkillDefinition(
        "uniq.basic", "uniq", "Remove adjacent duplicates", 1,
        description="Collapse adjacent duplicate lines.",
    ),
    "uniq.count": SkillDefinition(
        "uniq.count", "uniq", "Count duplicates (-c)", 2,
        ("uniq.basic",),
        "Prefix duplicate groups with their count.",
    ),
    "uniq.duplicates_only": SkillDefinition(
        "uniq.duplicates_only", "uniq", "Repeated groups only (-d)", 2,
        ("uniq.basic",),
        "Print one copy of each adjacent value that occurs more than once.",
    ),
    "uniq.unique_only": SkillDefinition(
        "uniq.unique_only", "uniq", "Unique groups only (-u)", 2,
        ("uniq.basic",),
        "Print only adjacent groups that occur exactly once.",
    ),
    "uniq.ignore_case": SkillDefinition(
        "uniq.ignore_case", "uniq", "Ignore case (-i)", 3,
        ("uniq.basic",),
        "Compare adjacent lines without case differences.",
    ),
    "uniq.skip_fields": SkillDefinition(
        "uniq.skip_fields", "uniq", "Skip fields (-f)", 3,
        ("uniq.basic",),
        "Ignore one or more leading fields when comparing adjacent lines.",
    ),

    # wc
    "wc.lines": SkillDefinition("wc.lines", "wc", "Count lines", 1),
    "wc.words": SkillDefinition("wc.words", "wc", "Count words", 1),
    "wc.bytes": SkillDefinition("wc.bytes", "wc", "Count bytes (-c)", 2, ("wc.lines",)),
    "wc.chars": SkillDefinition("wc.chars", "wc", "Count characters (-m)", 2, ("wc.words",)),
    "wc.multiple": SkillDefinition(
        "wc.multiple", "wc", "Multiple counts together", 2,
        description="Request more than one wc metric in a single command.",
    ),

    # sed
    "sed.substitute": SkillDefinition(
        "sed.substitute", "sed", "Substitution", 1,
        description="Replace one text pattern with another.",
    ),
    "sed.global": SkillDefinition(
        "sed.global", "sed", "Global substitution", 2,
        ("sed.substitute",),
        "Replace every matching occurrence on each line.",
    ),
    "sed.address": SkillDefinition(
        "sed.address", "sed", "Line / pattern addressing", 2,
        ("sed.substitute",),
        "Apply a sed command only to a selected line or matching address.",
    ),
    "sed.range": SkillDefinition(
        "sed.range", "sed", "Address ranges", 3,
        ("sed.address",),
        "Apply a command across a line or pattern range.",
    ),
    "sed.delete": SkillDefinition(
        "sed.delete", "sed", "Delete selected lines (d)", 2,
        description="Remove lines selected by an address or pattern.",
    ),
    "sed.print_only": SkillDefinition(
        "sed.print_only", "sed", "Selective printing (-n / p)", 2,
        description="Suppress default output and explicitly print selected lines.",
    ),
    "sed.backrefs": SkillDefinition(
        "sed.backrefs", "sed", "Capture groups & backreferences", 4,
        ("sed.substitute",),
        "Capture parts of a match and reuse them in the replacement.",
    ),
    "sed.multiple_expr": SkillDefinition(
        "sed.multiple_expr", "sed", "Multiple expressions (-e)", 3,
        ("sed.substitute",),
        "Apply several sed expressions in one command.",
    ),
    "sed.iac": SkillDefinition(
        "sed.iac", "sed", "Insert / append / change (i/a/c)", 4,
        ("sed.address",),
        "Insert, append, or replace whole lines at selected addresses.",
    ),

    # find
    "find.name_type": SkillDefinition(
        "find.name_type", "find", "Name & type filters", 1,
        description="Search recursively with -type and -name.",
    ),
    "find.size": SkillDefinition(
        "find.size", "find", "Size filters (-size)", 2,
        ("find.name_type",),
        "Select files by size using byte or larger size units.",
    ),
    "find.depth": SkillDefinition(
        "find.depth", "find", "Depth limits", 2,
        ("find.name_type",),
        "Limit traversal with -maxdepth or -mindepth.",
    ),
    "find.logic": SkillDefinition(
        "find.logic", "find", "Predicate logic", 3,
        ("find.name_type",),
        "Combine find predicates with AND, OR and NOT.",
    ),
    "find.exec": SkillDefinition(
        "find.exec", "find", "Actions with -exec", 4,
        ("find.name_type",),
        "Run another command for each path selected by find.",
    ),
    "find.path": SkillDefinition(
        "find.path", "find", "Path matching (-path)", 2,
        ("find.name_type",),
        "Match against the full relative path rather than only the basename.",
    ),

    # jq
    "jq.field": SkillDefinition(
        "jq.field", "jq", "Field extraction", 1,
        description="Extract values from JSON objects.",
    ),
    "jq.raw": SkillDefinition(
        "jq.raw", "jq", "Raw output (-r)", 1,
        ("jq.field",),
        "Print strings without JSON quotes.",
    ),
    "jq.select": SkillDefinition(
        "jq.select", "jq", "select() filtering", 2,
        ("jq.field",),
        "Filter JSON objects using a condition.",
    ),
    "jq.boolean": SkillDefinition(
        "jq.boolean", "jq", "Boolean logic", 3,
        ("jq.select",),
        "Combine JSON conditions with and, or and not.",
    ),
    "jq.multi_field": SkillDefinition(
        "jq.multi_field", "jq", "Multiple-field output", 2,
        ("jq.field",),
        "Emit more than one field from each JSON object in a controlled output shape.",
    ),
    "jq.arrays": SkillDefinition(
        "jq.arrays", "jq", "Arrays & indexing", 3,
        ("jq.field",),
        "Read array elements and construct or iterate JSON arrays.",
    ),
    "jq.length": SkillDefinition(
        "jq.length", "jq", "length", 3,
        ("jq.arrays",),
        "Count array elements or measure JSON strings/objects with length.",
    ),
    "jq.map": SkillDefinition(
        "jq.map", "jq", "map()", 4,
        ("jq.arrays",),
        "Apply an expression to every element of an array.",
    ),
    "jq.sort_by": SkillDefinition(
        "jq.sort_by", "jq", "sort_by()", 4,
        ("jq.arrays",),
        "Sort an array of JSON objects by a selected expression.",
    ),
    "jq.group_by": SkillDefinition(
        "jq.group_by", "jq", "group_by()", 5,
        ("jq.arrays",),
        "Group array elements by a JSON field or expression.",
    ),
    "jq.unique_by": SkillDefinition(
        "jq.unique_by", "jq", "unique_by()", 5,
        ("jq.arrays",),
        "Keep one object for each distinct value of a selected expression.",
    ),
    "jq.minmax": SkillDefinition(
        "jq.minmax", "jq", "min_by() / max_by()", 4,
        ("jq.arrays",),
        "Select the object with the minimum or maximum value for a field.",
    ),
    "jq.nested": SkillDefinition(
        "jq.nested", "jq", "Nested field paths", 3,
        ("jq.field",),
        "Traverse nested objects with chained .field paths.",
    ),
    "jq.construct": SkillDefinition(
        "jq.construct", "jq", "Construct objects", 4,
        ("jq.field",),
        "Build new JSON objects from selected or transformed fields.",
    ),

    # small pipeline utilities
    "head.basic": SkillDefinition("head.basic", "head", "Take first lines", 1),
    "head.bytes": SkillDefinition("head.bytes", "head", "Take first bytes (-c)", 2, ("head.basic",)),
    "tail.basic": SkillDefinition("tail.basic", "tail", "Take last lines", 1),
    "tail.from_line": SkillDefinition("tail.from_line", "tail", "Start at line N (-n +N)", 2, ("tail.basic",)),
    "tail.bytes": SkillDefinition("tail.bytes", "tail", "Take last bytes (-c)", 2, ("tail.basic",)),
    "cut.fields": SkillDefinition("cut.fields", "cut", "Delimited fields", 1),
    "cut.multiple_fields": SkillDefinition("cut.multiple_fields", "cut", "Multiple fields", 2, ("cut.fields",)),
    "cut.range": SkillDefinition("cut.range", "cut", "Field ranges", 2, ("cut.fields",)),
    "cut.complement": SkillDefinition("cut.complement", "cut", "Complement fields", 3, ("cut.fields",)),
    "cut.characters": SkillDefinition("cut.characters", "cut", "Character positions (-c)", 2),
}


TOOL_ORDER = [
    "awk", "grep", "sort", "uniq", "sed", "find", "jq",
    "wc", "head", "tail", "cut", "shell",
]

STATUS_ORDER = {
    "not_introduced": 0,
    "introduced": 1,
    "learning": 2,
    "practiced": 3,
    "comfortable": 4,
}

STATUS_LABELS = {
    "not_introduced": "Not introduced",
    "introduced": "Introduced",
    "learning": "Learning",
    "practiced": "Practiced",
    "comfortable": "Comfortable",
}


def _legacy_skill_ids(record: dict) -> set[str]:
    """Best-effort inference so old Console Chaos/ShellGym history still counts."""
    command = str(record.get("accepted_answer", ""))
    tools = set(record.get("tools", []))
    found: set[str] = set()

    if "awk" in tools or "awk" in command:
        found.add("awk.fields")
        if re.search(r"awk\s+-F", command):
            found.add("awk.separator")
        if re.search(r"\$\d+\s*(==|!=|>=|<=|>|<)", command) or "&&" in command or "||" in command:
            found.add("awk.conditions")
        if re.search(r"\b(NR|NF)\b", command):
            found.add("awk.nr_nf")
        if re.search(r"awk\s+['\"]?/", command) or "~" in command:
            found.add("awk.regex")
        if "END" in command or re.search(r"\b[a-zA-Z_]\w*\+\+", command):
            found.add("awk.variables_end")
        if re.search(r"\bfor\s*\(", command):
            found.add("awk.loops")
        if re.search(r"\$i\b|\$\(i\s*[+-]", command):
            found.add("awk.dynamic_fields")
        if "split(" in command:
            found.add("awk.split")
        if "sub(" in command or "gsub(" in command:
            found.add("awk.substitution")
        if re.search(r"\w+\[[^]]+\]\+\+", command):
            found.add("awk.assoc_arrays")

    if "grep" in tools or "grep" in command:
        found.add("grep.literal")
        if re.search(r"grep\s+[^|\n]*-v", command):
            found.add("grep.invert")
        if re.search(r"grep\s+[^|\n]*-E", command):
            found.add("grep.extended")
            found.add("grep.regex")
        elif re.search(r"grep\s+[^|\n]*['\"][^'\"]*[\^$\[\].*+?()|]", command):
            found.add("grep.regex")

    if "sort" in tools or "sort" in command:
        found.add("sort.basic")
        if re.search(r"sort\s+[^|\n]*-u", command):
            found.add("sort.unique")
        if re.search(r"sort\s+[^|\n]*-[^\s|]*[nr]", command):
            found.add("sort.numeric_reverse")
        keys = re.findall(r"(?:^|\s)-k", command)
        if keys:
            found.add("sort.keys")
        if len(keys) >= 2:
            found.add("sort.multiple_keys")

    if "uniq" in tools or "uniq" in command:
        found.add("uniq.basic")
        if "uniq -c" in command:
            found.add("uniq.count")

    if "sed" in tools or "sed" in command:
        found.add("sed.substitute")
        if re.search(r"s/.+/.+/g", command):
            found.add("sed.global")

    if "find" in tools or re.search(r"(^|\|)\s*find\b", command):
        found.add("find.name_type")

    if "jq" in tools or "jq" in command:
        found.add("jq.field")
        if "-r" in command:
            found.add("jq.raw")
        if "select(" in command:
            found.add("jq.select")

    if "wc" in tools or "wc" in command:
        if "wc -l" in command:
            found.add("wc.lines")
        if "wc -w" in command:
            found.add("wc.words")

    if "head" in tools or "head " in command:
        found.add("head.basic")
    if "tail" in tools or "tail " in command:
        found.add("tail.basic")
    if "cut" in tools or "cut " in command:
        found.add("cut.fields")

    pipe_count = command.count("|")
    if pipe_count >= 1:
        found.add("shell.pipeline.basic")
    if pipe_count >= 2:
        found.add("shell.pipeline.multi")
    if re.search(r"(^|\s)<\s*\S+", command):
        found.add("shell.redirection.input")

    return {skill_id for skill_id in found if skill_id in SKILLS}


def record_skill_uses(record: dict) -> list[dict]:
    """Return skills actually demonstrated by the accepted command.

    New records save this explicitly. Older records are re-analysed from their
    accepted answer so intended exercise targets are not mistaken for evidence.
    """
    explicit = record.get("demonstrated_skills")
    if isinstance(explicit, list) and explicit:
        valid = []
        for item in explicit:
            if not isinstance(item, dict):
                continue
            skill_id = item.get("skill_id") or item.get("id")
            if skill_id in SKILLS:
                valid.append({
                    "skill_id": skill_id,
                    "role": item.get("role", "demonstrated"),
                })
        if valid:
            return valid

    declared_roles = {}
    for item in record.get("skills", []) or []:
        if isinstance(item, dict):
            skill_id = item.get("skill_id") or item.get("id")
            if skill_id in SKILLS:
                declared_roles[skill_id] = item.get("role", "reinforcement")

    command = str(record.get("accepted_answer", ""))
    detected = sorted(
        skill_id for skill_id in detect_command_skills(command)
        if skill_id in SKILLS
    )
    if detected:
        return [
            {
                "skill_id": skill_id,
                "role": declared_roles.get(skill_id, "demonstrated"),
            }
            for skill_id in detected
        ]

    return [
        {"skill_id": skill_id, "role": declared_roles.get(skill_id, "legacy")}
        for skill_id in sorted(_legacy_skill_ids(record))
    ]


def build_progress(records: list[dict]) -> dict[str, dict]:
    evidence: dict[str, dict] = {
        skill_id: {
            "skill_id": skill_id,
            "appearances": 0,
            "target_successes": 0,
            "integration_uses": 0,
            "challenge_uses": 0,
            "datasets": set(),
            "exercise_ids": [],
        }
        for skill_id in SKILLS
    }

    # list_records() is newest-first. Reverse it for chronological evidence.
    for record in reversed(records):
        style = record.get("style", "legacy")
        dataset = record.get("dataset_kind", "unknown")
        rid = record.get("id")

        for use in record_skill_uses(record):
            skill_id = use["skill_id"]
            item = evidence[skill_id]
            item["appearances"] += 1
            item["datasets"].add(dataset)
            if rid is not None:
                item["exercise_ids"].append(rid)
            if use.get("role") == "target":
                item["target_successes"] += 1
            if style == "integration":
                item["integration_uses"] += 1
            elif style == "challenge":
                item["challenge_uses"] += 1

    progress: dict[str, dict] = {}

    for skill_id, item in evidence.items():
        appearances = item["appearances"]
        dataset_count = len(item["datasets"])
        applied = item["integration_uses"] + item["challenge_uses"]

        if appearances == 0:
            status = "not_introduced"
        elif appearances == 1:
            status = "introduced"
        elif appearances <= 2:
            status = "learning"
        elif appearances >= 5 and dataset_count >= 2 and applied >= 1:
            status = "comfortable"
        else:
            status = "practiced"

        definition = SKILLS[skill_id]
        progress[skill_id] = {
            **item,
            "datasets": sorted(item["datasets"]),
            "dataset_count": dataset_count,
            "status": status,
            "status_rank": STATUS_ORDER[status],
            "status_label": STATUS_LABELS[status],
            "name": definition.name,
            "tool": definition.tool,
            "level": definition.level,
            "requires": list(definition.requires),
            "description": definition.description,
        }

    return progress


def prerequisites_ready(skill_id: str, progress: dict[str, dict]) -> bool:
    definition = SKILLS[skill_id]
    if not definition.requires:
        return True
    return all(
        progress[required]["status_rank"] >= STATUS_ORDER["learning"]
        for required in definition.requires
    )


def skill_tree(records: list[dict]) -> dict:
    progress = build_progress(records)
    by_tool: dict[str, list[dict]] = defaultdict(list)

    for skill_id, definition in SKILLS.items():
        node = dict(progress[skill_id])
        node["ready"] = prerequisites_ready(skill_id, progress)
        node["requires_names"] = [SKILLS[r].name for r in definition.requires]
        by_tool[definition.tool].append(node)

    ordered_tools = []
    seen = set()
    for tool in TOOL_ORDER + sorted(by_tool):
        if tool in seen or tool not in by_tool:
            continue
        seen.add(tool)
        nodes = sorted(by_tool[tool], key=lambda x: (x["level"], x["name"]))
        ordered_tools.append({
            "tool": tool,
            "nodes": nodes,
            "completed": sum(n["status_rank"] >= STATUS_ORDER["practiced"] for n in nodes),
            "total": len(nodes),
        })

    summary = {
        "solved": len(records),
        "comfortable": sum(p["status"] == "comfortable" for p in progress.values()),
        "practiced": sum(p["status"] == "practiced" for p in progress.values()),
        "learning": sum(p["status"] in {"introduced", "learning"} for p in progress.values()),
        "not_introduced": sum(p["status"] == "not_introduced" for p in progress.values()),
    }

    ready_next = [
        progress[skill_id]
        for skill_id in SKILLS
        if progress[skill_id]["status"] == "not_introduced"
        and prerequisites_ready(skill_id, progress)
    ]
    ready_next.sort(key=lambda x: (x["level"], TOOL_ORDER.index(x["tool"]) if x["tool"] in TOOL_ORDER else 999, x["name"]))

    return {
        "tools": ordered_tools,
        "summary": summary,
        "ready_next": ready_next[:8],
        "progress": progress,
    }
