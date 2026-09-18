from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace

from .models import Dataset, Exercise
from .tasks import make, output, skill


def _with_files(ds: Dataset, **files: str) -> Dataset:
    return replace(ds, files={**ds.files, **files})


def _lines(text: str) -> list[str]:
    return text.rstrip("\n").splitlines()


def _line_text(items: list[str]) -> str:
    return "\n".join(items) + ("\n" if items else "")


def _add(items: list[Exercise], exercise: Exercise) -> None:
    items.append(exercise)


def _words_exercises(ds: Dataset) -> list[Exercise]:
    ex: list[Exercise] = []
    words_text = ds.files["words.txt"]
    words = _lines(words_text)

    _add(ex, make(
        "expanded.words.wc_bytes",
        "Count bytes",
        'Print only the byte count of "words.txt".',
        "focused",
        ["wc"],
        [skill("wc.bytes"), skill("shell.redirection.input", "reinforcement")],
        output("ONE NUMBER", "128", "Print exactly one number.", "Do not print the filename."),
        ds,
        str(len(words_text.encode("utf-8"))),
        "wc -c < words.txt",
        "`wc -c` counts bytes. Input redirection avoids the filename suffix that wc prints when a pathname is supplied directly.",
    ))

    unicode_text = "café\nnaïve\nrésumé\n東京\n"
    uds = _with_files(ds, **{"unicode.txt": unicode_text})
    _add(ex, make(
        "expanded.words.wc_chars",
        "Count Unicode characters",
        'Print only the number of characters in "unicode.txt". Count characters, not bytes.',
        "focused",
        ["wc"],
        [skill("wc.chars"), skill("shell.redirection.input", "reinforcement")],
        output("ONE NUMBER", "18", "Print exactly one number.", "Characters and bytes are intentionally different here."),
        uds,
        str(len(unicode_text)),
        "wc -m < unicode.txt",
        "`wc -m` counts characters in the current UTF-8 locale; `wc -c` would count the encoded bytes instead.",
    ))

    word_count = sum(len(line.split()) for line in words)
    wc_width = len(str(len(words_text.encode("utf-8"))))
    wc_multi_expected = f"{len(words):>{wc_width}} {word_count:>{wc_width}}".lstrip()
    _add(ex, make(
        "expanded.words.wc_multiple",
        "Count lines and words together",
        'From "words.txt", print the line count followed by the word count using one `wc` command.',
        "focused",
        ["wc"],
        [skill("wc.multiple"), skill("wc.lines", "reinforcement"), skill("wc.words", "reinforcement"), skill("shell.redirection.input", "reinforcement")],
        output("LINES WORDS", "32 32", "Print exactly two numbers on one line.", "Do not print the filename."),
        ds,
        wc_multi_expected,
        "wc -lw < words.txt",
        "`wc` can combine options; with `-l` and `-w` it reports line and word counts together.",
    ))

    first_bytes = words_text.encode("utf-8")[:12].decode("utf-8")
    _add(ex, make(
        "expanded.words.head_bytes",
        "Take the first bytes",
        'Print exactly the first 12 bytes of "words.txt".',
        "focused",
        ["head"],
        [skill("head.bytes"), skill("head.basic", "reinforcement")],
        output("RAW PREFIX", "kernel\nnetw", "Print exactly the byte prefix; do not add labels."),
        ds,
        first_bytes,
        "head -c 12 words.txt",
        "`head -c N` switches from line-oriented output to the first N bytes.",
    ))

    last_bytes = words_text.encode("utf-8")[-12:].decode("utf-8")
    from_line_expected = "\n".join(words[3:])
    _add(ex, make(
        "expanded.words.tail_from_line",
        "Start output at a chosen line",
        "From \"words.txt\", print from line 4 through the end using tail's `+N` form.",
        "focused",
        ["tail"],
        [skill("tail.from_line"), skill("tail.basic", "reinforcement")],
        output("LINES 4 THROUGH END", "fourth\nfifth\n...", "Line 4 must be the first output line."),
        ds,
        from_line_expected,
        "tail -n +4 words.txt",
        "`tail -n +4` means start at input line 4, not take the last four lines.",
    ))

    _add(ex, make(
        "expanded.words.tail_bytes",
        "Take the last bytes",
        'Print exactly the last 12 bytes of "words.txt".',
        "focused",
        ["tail"],
        [skill("tail.bytes"), skill("tail.basic", "reinforcement")],
        output("RAW SUFFIX", "server\nlinux", "Print exactly the byte suffix; do not add labels."),
        ds,
        last_bytes,
        "tail -c 12 words.txt",
        "`tail -c N` emits bytes from the end instead of lines from the end.",
    ))

    first3 = "\n".join(words[:3])
    _add(ex, make(
        "expanded.words.redirect_output",
        "Redirect stdout to a file",
        'Write the first 3 lines of "words.txt" to "selected.txt" using output redirection, then print "selected.txt".',
        "focused",
        ["head", "cat"],
        [skill("shell.redirection.output"), skill("head.basic", "reinforcement")],
        output("THREE LINES", "alpha\nbeta\ngamma", "The final stdout must contain only the three selected lines."),
        ds,
        first3,
        "head -n 3 words.txt > selected.txt; cat selected.txt",
        "`>` sends stdout into the destination file. Printing the file afterward proves the redirected contents.",
    ))

    append_expected = f"{words[0]}\n{words[-1]}"
    _add(ex, make(
        "expanded.words.redirect_append",
        "Append to redirected output",
        'Create "selected.txt" with the first line of "words.txt", append the last line with `>>`, then print "selected.txt".',
        "focused",
        ["head", "tail", "cat"],
        [skill("shell.redirection.append"), skill("shell.redirection.output", "reinforcement")],
        output("TWO LINES", "first\nlast", "The original first line must remain when the last line is appended."),
        ds,
        append_expected,
        "head -n 1 words.txt > selected.txt; tail -n 1 words.txt >> selected.txt; cat selected.txt",
        "A single `>` creates/replaces the file; `>>` appends later stdout without removing what is already there.",
    ))

    _add(ex, make(
        "expanded.words.redirect_stderr",
        "Redirect standard error",
        'Run `cat` on missing file "missing.txt" and then "words.txt", but suppress only the error output. Stdout must still be the contents of "words.txt".',
        "focused",
        ["cat", "true"],
        [skill("shell.redirection.stderr")],
        output("FILE CONTENT", "kernel\nnetwork\n...", "Do not print the missing-file error."),
        ds,
        words_text.rstrip("\n"),
        "cat missing.txt words.txt 2>/dev/null; true",
        "`2>` redirects file descriptor 2 (stderr) while leaving normal stdout untouched.",
    ))

    _add(ex, make(
        "expanded.words.shell_and",
        "Run a command only after success",
        'If "words.txt" exists and is non-empty, print its first line using `&&`.',
        "focused",
        ["test", "head"],
        [skill("shell.boolean.and"), skill("head.basic", "reinforcement")],
        output("ONE LINE", "kernel", "Print only the first line."),
        ds,
        words[0],
        "test -s words.txt && head -n 1 words.txt",
        "With `&&`, the right-hand command runs only if the left-hand test succeeds.",
    ))

    _add(ex, make(
        "expanded.words.shell_or",
        "Run a fallback after failure",
        'Use `||` so that when "missing.txt" does not exist, the first line of "words.txt" is printed.',
        "focused",
        ["test", "head"],
        [skill("shell.boolean.or"), skill("head.basic", "reinforcement")],
        output("ONE LINE", "kernel", "Print only the first line of words.txt."),
        ds,
        words[0],
        "test -f missing.txt || head -n 1 words.txt",
        "With `||`, the fallback runs only because the first command exits unsuccessfully.",
    ))

    seq_expected = f"{words[0]}\n{words[-1]}"
    _add(ex, make(
        "expanded.words.shell_sequence",
        "Sequence two commands",
        'Print the first line of "words.txt", then the last line, using `;` to separate the commands.',
        "focused",
        ["head", "tail"],
        [skill("shell.sequence"), skill("head.basic", "reinforcement"), skill("tail.basic", "reinforcement")],
        output("TWO LINES", "first\nlast", "First line first, last line second."),
        ds,
        seq_expected,
        "head -n 1 words.txt; tail -n 1 words.txt",
        "A semicolon runs the second command after the first without making it conditional on success.",
    ))

    grouped_expected = "\n".join(sorted([words[0], words[-1]]))
    _add(ex, make(
        "expanded.words.shell_subshell",
        "Group command output",
        'Group commands that print the first and last lines of "words.txt" in a subshell, then sort the combined output.',
        "focused",
        ["head", "tail", "sort"],
        [skill("shell.subshell"), skill("shell.pipeline.basic", "reinforcement"), skill("sort.basic", "reinforcement")],
        output("TWO SORTED LINES", "alpha\nzeta", "Sort the combined output as one stream."),
        ds,
        grouped_expected,
        "(head -n 1 words.txt; tail -n 1 words.txt) | sort",
        "Parentheses group both producers so their combined stdout becomes the left side of one pipeline.",
    ))

    # Controlled fixtures for advanced sort/sed/cut concepts.
    sizes = ["900K", "12M", "2G", "512K", "4G", "3M"]
    sds = _with_files(ds, **{"sizes.txt": _line_text(sizes)})
    _add(ex, make(
        "expanded.words.sort_human",
        "Sort human-readable sizes",
        'Sort "sizes.txt" from smallest to largest by magnitude.',
        "focused",
        ["sort"],
        [skill("sort.human"), skill("sort.basic", "reinforcement")],
        output("ONE SIZE PER LINE", "512K\n3M\n2G", "Use numeric magnitude, not ordinary text order."),
        sds,
        "512K\n900K\n3M\n12M\n2G\n4G",
        "sort -h sizes.txt",
        "`sort -h` understands K/M/G suffixes and compares their numeric magnitude.",
    ))

    versions = ["v1.10", "v1.2", "v2.0", "v1.2.1", "v1.9", "v10.0"]
    vds = _with_files(ds, **{"versions.txt": _line_text(versions)})
    _add(ex, make(
        "expanded.words.sort_version",
        "Sort version strings",
        'Sort "versions.txt" in version order.',
        "focused",
        ["sort"],
        [skill("sort.version"), skill("sort.basic", "reinforcement")],
        output("ONE VERSION PER LINE", "v1.2\nv1.9\nv1.10", "Use version-aware ordering."),
        vds,
        "v1.2\nv1.2.1\nv1.9\nv1.10\nv2.0\nv10.0",
        "sort -V versions.txt",
        "`sort -V` compares embedded numeric components naturally, so 1.10 follows 1.9 rather than 1.1.",
    ))

    months = ["Dec report", "Feb report", "Jan report", "Oct report", "Apr report", "Aug report"]
    mds = _with_files(ds, **{"months.txt": _line_text(months)})
    _add(ex, make(
        "expanded.words.sort_month",
        "Sort by month",
        'Sort "months.txt" by the leading month name in calendar order.',
        "focused",
        ["sort"],
        [skill("sort.month"), skill("sort.basic", "reinforcement")],
        output("MONTH RECORDS", "Jan report\nFeb report\nApr report", "Use calendar month order."),
        mds,
        "Jan report\nFeb report\nApr report\nAug report\nOct report\nDec report",
        "sort -M months.txt",
        "`sort -M` recognizes month abbreviations instead of ordering them alphabetically.",
    ))

    sed_lines = ["alpha x", "alpha x x", "beta x", "gamma x x", "delta x"]
    sed_text = _line_text(sed_lines)
    sed_ds = _with_files(ds, **{"sed_lines.txt": sed_text})
    addressed = sed_lines.copy(); addressed[1] = addressed[1].replace("alpha", "ALPHA", 1)
    _add(ex, make(
        "expanded.words.sed_address",
        "Substitute on one addressed line",
        'In "sed_lines.txt", replace `alpha` with `ALPHA` only on line 2 and print the resulting full file.',
        "focused",
        ["sed"],
        [skill("sed.address"), skill("sed.substitute", "reinforcement")],
        output("TRANSFORMED FILE", "alpha x\nALPHA x x\n...", "Only line 2 is eligible for replacement."),
        sed_ds,
        "\n".join(addressed),
        "sed '2s/alpha/ALPHA/' sed_lines.txt",
        "The numeric address `2` limits the substitution command to the second input line.",
    ))

    ranged = [line.replace("x", "X") if 1 <= i <= 3 else line for i, line in enumerate(sed_lines)]
    _add(ex, make(
        "expanded.words.sed_range",
        "Transform an addressed range",
        'In "sed_lines.txt", replace every `x` with `X` only on lines 2 through 4.',
        "focused",
        ["sed"],
        [skill("sed.range"), skill("sed.global", "reinforcement")],
        output("TRANSFORMED FILE", "alpha x\nalpha X X\nbeta X\n...", "Only lines 2-4 are transformed.", "Replace every x on those lines."),
        sed_ds,
        "\n".join(ranged),
        "sed '2,4s/x/X/g' sed_lines.txt",
        "`2,4` selects a range and `g` replaces every occurrence on each selected line.",
    ))

    pairs = ["alice:web-01", "bob:db-01", "carol:worker-02"]
    pds = _with_files(ds, **{"pairs.txt": _line_text(pairs)})
    pair_expected = "\n".join(f"{host} {user}" for user, host in (line.split(":", 1) for line in pairs))
    _add(ex, make(
        "expanded.words.sed_backrefs",
        "Reorder captured text",
        'From "pairs.txt", transform each `USER:HOST` line into `HOST USER` using sed capture groups.',
        "focused",
        ["sed"],
        [skill("sed.backrefs"), skill("sed.substitute", "reinforcement")],
        output("HOST USER", "web-01 alice", "One transformed pair per line."),
        pds,
        pair_expected,
        r"sed -E 's/^([^:]+):(.+)$/\2 \1/' pairs.txt",
        "The two capture groups remember USER and HOST; the replacement emits group 2 before group 1.",
    ))

    levels = ["INFO request", "WARN retry", "ERROR failure", "INFO health"]
    lds = _with_files(ds, **{"levels.txt": _line_text(levels)})
    _add(ex, make(
        "expanded.words.sed_multiple_expr",
        "Apply multiple sed expressions",
        'From "levels.txt", replace `INFO` with `I` and `WARN` with `W` using two `-e` expressions.',
        "focused",
        ["sed"],
        [skill("sed.multiple_expr"), skill("sed.substitute", "reinforcement")],
        output("TRANSFORMED FILE", "I request\nW retry\nERROR failure", "Apply both substitutions in one sed command."),
        lds,
        "I request\nW retry\nERROR failure\nI health",
        "sed -e 's/INFO/I/' -e 's/WARN/W/' levels.txt",
        "Each `-e` contributes one sed program; both are applied in order to the same stream.",
    ))

    changed = sed_lines.copy(); changed[1] = "REPLACED"
    _add(ex, make(
        "expanded.words.sed_iac",
        "Replace a whole line",
        'In "sed_lines.txt", replace the entire second line with the literal text `REPLACED` using sed\'s change command.',
        "focused",
        ["sed"],
        [skill("sed.iac"), skill("sed.address", "reinforcement")],
        output("TRANSFORMED FILE", "alpha x\nREPLACED\nbeta x\n...", "Replace the whole line, not just one word."),
        sed_ds,
        "\n".join(changed),
        r"sed '2c\REPLACED' sed_lines.txt",
        "The address selects line 2 and `c\\` replaces that whole line with new text.",
    ))

    first3chars = "\n".join(line[:3] for line in words)
    _add(ex, make(
        "expanded.words.cut_chars",
        "Extract fixed character positions",
        'From "words.txt", print the first 3 characters of every line.',
        "focused",
        ["cut"],
        [skill("cut.characters")],
        output("THREE CHARACTERS PER LINE", "ker\nnet\nlin", "Preserve input order."),
        ds,
        first3chars,
        "cut -c1-3 words.txt",
        "`cut -c1-3` selects fixed character positions rather than delimiter-based fields.",
    ))

    return ex


def _auth_exercises(ds: Dataset) -> list[Exercise]:
    ex: list[Exercise] = []
    rows = _lines(ds.files["auth.log"])

    failed = [line for line in rows if "Failed password" in line]
    _add(ex, make(
        "expanded.auth.grep_ignore_case",
        "Match without case sensitivity",
        'From "auth.log", print lines containing `failed password` even though the log capitalizes the text.',
        "focused",
        ["grep"],
        [skill("grep.ignore_case"), skill("grep.literal", "reinforcement")],
        output("MATCHING LOG LINES", "... Failed password ...", "Preserve input order."),
        ds,
        "\n".join(failed),
        "grep -i 'failed password' auth.log",
        "`-i` makes the lowercase search pattern match the capitalized log message.",
    ))

    _add(ex, make(
        "expanded.auth.grep_count",
        "Count matching log lines with grep",
        'Print only the number of lines in "auth.log" containing `Failed password` using grep\'s own count option.',
        "focused",
        ["grep"],
        [skill("grep.count"), skill("grep.literal", "reinforcement")],
        output("ONE NUMBER", "17", "Print exactly one number."),
        ds,
        str(len(failed)),
        "grep -c 'Failed password' auth.log",
        "`grep -c` reports the number of matching lines directly.",
    ))

    word_matches = [line for line in rows if " invalid user " in line]
    if word_matches:
        _add(ex, make(
            "expanded.auth.grep_word",
            "Match a whole word",
            'From "auth.log", print lines containing the whole word `invalid`.',
            "focused",
            ["grep"],
            [skill("grep.word"), skill("grep.literal", "reinforcement")],
            output("MATCHING LOG LINES", "... invalid user ...", "Preserve input order."),
            ds,
            "\n".join(word_matches),
            "grep -w 'invalid' auth.log",
            "`-w` requires `invalid` to be bounded as a complete word.",
        ))

    any_two = [line for line in rows if "invalid user" in line or "Accepted publickey" in line]
    _add(ex, make(
        "expanded.auth.grep_multiple_patterns",
        "Match either of two patterns",
        'From "auth.log", print lines containing either `invalid user` or `Accepted publickey` using separate grep patterns.',
        "focused",
        ["grep"],
        [skill("grep.multiple_patterns"), skill("grep.literal", "reinforcement")],
        output("MATCHING LOG LINES", "... invalid user ...\n... Accepted publickey ...", "Preserve input order."),
        ds,
        "\n".join(any_two),
        "grep -e 'invalid user' -e 'Accepted publickey' auth.log",
        "Multiple `-e` options make grep accept a line when either pattern matches.",
    ))

    return ex


def _config_exercises(ds: Dataset) -> list[Exercise]:
    ex: list[Exercise] = []
    rows = _lines(ds.files["service.conf"])

    literal_text = "[api] ready\napi ready\n[db] ready\n[api] failed\n"
    lds = _with_files(ds, **{"literal.txt": literal_text})
    _add(ex, make(
        "expanded.config.grep_fixed",
        "Match literal regex characters",
        'From "literal.txt", print lines containing the literal text `[api]`. Treat the brackets as ordinary characters.',
        "focused",
        ["grep"],
        [skill("grep.fixed"), skill("grep.literal", "reinforcement")],
        output("MATCHING LINES", "[api] ready\n[api] failed", "Preserve input order."),
        lds,
        "[api] ready\n[api] failed",
        "grep -F '[api]' literal.txt",
        "`-F` disables regex interpretation, so square brackets are matched literally.",
    ))

    port_index = next(i for i, line in enumerate(rows, 1) if line.startswith("PORT="))
    port_line = rows[port_index - 1]
    _add(ex, make(
        "expanded.config.grep_line_numbers",
        "Show matching line numbers",
        'From "service.conf", print the `PORT=` assignment prefixed by its line number.',
        "focused",
        ["grep"],
        [skill("grep.line_numbers"), skill("grep.regex", "reinforcement")],
        output("LINE_NUMBER:LINE", "5:PORT=8080", "Print grep's standard `line:content` form."),
        ds,
        f"{port_index}:{port_line}",
        "grep -n '^PORT=' service.conf",
        "`-n` prefixes matching lines with their 1-based line number.",
    ))

    context = rows[port_index - 1: min(port_index + 1, len(rows))]
    _add(ex, make(
        "expanded.config.grep_context",
        "Show context after a match",
        'From "service.conf", print the `PORT=` line and exactly one following line using grep context.',
        "focused",
        ["grep"],
        [skill("grep.context"), skill("grep.regex", "reinforcement")],
        output("MATCH PLUS ONE FOLLOWING LINE", "PORT=8080\n# next setting", "Preserve the file text exactly."),
        ds,
        "\n".join(context),
        "grep -A 1 '^PORT=' service.conf",
        "`-A 1` includes one line after each match.",
    ))

    no_comments = [line for line in rows if not line.lstrip().startswith("#")]
    _add(ex, make(
        "expanded.config.sed_delete",
        "Delete comment lines",
        'From "service.conf", print the file with comment lines removed. Preserve blank lines.',
        "focused",
        ["sed"],
        [skill("sed.delete")],
        output("CONFIG WITHOUT COMMENTS", "\nPORT=8080\n...", "Preserve blank lines and assignment order."),
        ds,
        "\n".join(no_comments),
        r"sed '/^[[:space:]]*#/d' service.conf",
        "The regex addresses comment lines and the `d` command removes those lines from sed output.",
    ))

    assignments = [line for line in rows if "=" in line and not line.lstrip().startswith("#")]
    _add(ex, make(
        "expanded.config.sed_print_only",
        "Print selected lines with sed",
        'From "service.conf", print only active assignment lines containing `=` using sed selective printing.',
        "focused",
        ["sed"],
        [skill("sed.print_only")],
        output("ASSIGNMENT LINES", "PORT=8080\nWORKERS=4", "Do not print comments or blank lines."),
        ds,
        "\n".join(assignments),
        "sed -n '/=/p' service.conf",
        "`-n` suppresses normal output and `p` emits only lines selected by the address.",
    ))

    return ex


def _filetree_exercises(ds: Dataset) -> list[Exercise]:
    ex: list[Exercise] = []
    paths = list(ds.files)

    _add(ex, make(
        "expanded.filetree.grep_recursive",
        "Search a directory tree recursively",
        'From the exercise directory, recursively find files containing the text `old` and print only their paths, sorted normally.',
        "focused",
        ["grep", "sort"],
        [skill("grep.recursive"), skill("sort.basic", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("ONE PATH PER LINE", "./logs/archive/app-1.log", "Paths must begin with `./`.", "Sort normally."),
        ds,
        "./logs/archive/app-1.log",
        "grep -rl 'old' . | sort",
        "`grep -r` descends directories and `-l` prints matching filenames instead of matching lines.",
    ))

    large = sorted(f"./{path}" for path, content in ds.files.items() if len(content.encode("utf-8")) > 10)
    if large:
        _add(ex, make(
            "expanded.filetree.find_size",
            "Find files by byte size",
            'From the exercise directory, print regular files larger than 10 bytes, sorted using normal text order.',
            "focused",
            ["find", "sort"],
            [skill("find.size"), skill("find.name_type", "reinforcement"), skill("sort.basic", "reinforcement")],
            output("ONE PATH PER LINE", "./data/users.csv", "Paths begin with `./`.", "Sort normally."),
            ds,
            "\n".join(large),
            "find . -type f -size +10c | sort",
            "`-size +10c` means strictly larger than 10 bytes; `c` selects byte units.",
        ))

    depth2 = sorted(f"./{path}" for path in paths if len(path.split("/")) <= 2)
    _add(ex, make(
        "expanded.filetree.find_depth",
        "Limit recursive depth",
        'Print regular files no deeper than depth 2 below `.` and sort the paths.',
        "focused",
        ["find", "sort"],
        [skill("find.depth"), skill("find.name_type", "reinforcement"), skill("sort.basic", "reinforcement")],
        output("ONE PATH PER LINE", "./README.txt\n./data/users.csv", "Paths begin with `./`.", "Do not include deeper descendants."),
        ds,
        "\n".join(depth2),
        "find . -maxdepth 2 -type f | sort",
        "The starting directory is depth 0, so `-maxdepth 2` includes files directly inside one child directory but not deeper trees.",
    ))

    logic = sorted(f"./{path}" for path in paths if path.endswith(".log") or path.endswith(".json"))
    _add(ex, make(
        "expanded.filetree.find_logic",
        "Combine find predicates with OR",
        'Print regular files whose names end in `.log` OR `.json`, sorted normally.',
        "focused",
        ["find", "sort"],
        [skill("find.logic"), skill("find.name_type", "reinforcement"), skill("sort.basic", "reinforcement")],
        output("ONE PATH PER LINE", "./data/events.json\n./logs/app.log", "Paths begin with `./`.", "Sort normally."),
        ds,
        "\n".join(logic),
        "find . -type f -name '*.log' -o -type f -name '*.json' | sort",
        "Escaped parentheses group the OR alternatives so `-type f` applies to both branches.",
    ))

    log_basenames = sorted(path.rsplit("/", 1)[-1] for path in paths if path.endswith(".log"))
    _add(ex, make(
        "expanded.filetree.find_exec",
        "Run an action for found files",
        'For every `.log` file, use `find -exec` to print only its basename, then sort the names.',
        "focused",
        ["find", "sort"],
        [skill("find.exec"), skill("find.name_type", "reinforcement"), skill("sort.basic", "reinforcement")],
        output("ONE BASENAME PER LINE", "access.log\napp.log", "Do not include directory prefixes.", "Sort normally."),
        ds,
        "\n".join(log_basenames),
        "find . -type f -name '*.log' -exec basename {} \\; | sort",
        "`-exec` substitutes each selected pathname at `{}` and runs `basename` for it.",
    ))

    nginx_paths = sorted(f"./{path}" for path in paths if path.startswith("logs/nginx/") and path.count("/") >= 2)
    _add(ex, make(
        "expanded.filetree.find_path",
        "Match a full path",
        'Print regular files under `./logs/nginx/` using `find -path`, sorted normally.',
        "focused",
        ["find", "sort"],
        [skill("find.path"), skill("find.name_type", "reinforcement"), skill("sort.basic", "reinforcement")],
        output("ONE PATH PER LINE", "./logs/nginx/access.log\n./logs/nginx/error.log", "Paths begin with `./`."),
        ds,
        "\n".join(nginx_paths),
        "find . -type f -path './logs/nginx/*' | sort",
        "`-path` tests the complete pathname emitted by find, including directory components.",
    ))

    return ex


def _requests_exercises(ds: Dataset) -> list[Exercise]:
    ex: list[Exercise] = []
    rows = _lines(ds.files["requests.csv"])
    data = rows[1:]

    sorted_rows = sorted(data, key=lambda line: (int(line.split(",")[4]), line.split(",")[1], line))
    _add(ex, make(
        "expanded.requests.sort_delimiter",
        "Sort CSV by a delimited key",
        'From "requests.csv", skip the header and sort rows by STATUS numerically, then by IP using normal text order.',
        "focused",
        ["tail", "sort"],
        [skill("sort.delimiter"), skill("sort.keys", "reinforcement"), skill("sort.numeric_reverse", "reinforcement"), skill("tail.from_line", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("CSV DATA ROWS", "01:00:00,10.0.0.8,GET,/,200,512,30", "Do not print the header.", "STATUS ascending; IP breaks ties."),
        ds,
        "\n".join(sorted_rows),
        "tail -n +2 requests.csv | sort -t, -k5,5n -k2,2",
        "`-t,` makes comma the sort field delimiter so `-k5,5n` refers to the STATUS column.",
    ))

    cols = [line.split(",") for line in data]
    _add(ex, make(
        "expanded.requests.cut_multiple",
        "Extract non-adjacent CSV fields",
        'From "requests.csv", skip the header and print `IP,STATUS` for every data row using cut.',
        "focused",
        ["tail", "cut"],
        [skill("cut.multiple_fields"), skill("cut.fields", "reinforcement"), skill("tail.from_line", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("IP,STATUS", "10.0.0.8,404", "Preserve input order.", "Do not print the header."),
        ds,
        "\n".join(f"{c[1]},{c[4]}" for c in cols),
        "tail -n +2 requests.csv | cut -d, -f2,5",
        "Comma-separated field numbers let cut emit non-adjacent columns in one command.",
    ))

    _add(ex, make(
        "expanded.requests.cut_range",
        "Extract a CSV field range",
        'From "requests.csv", skip the header and print columns 2 through 4 (`IP,METHOD,PATH`) for each row.',
        "focused",
        ["tail", "cut"],
        [skill("cut.range"), skill("cut.fields", "reinforcement"), skill("tail.from_line", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("IP,METHOD,PATH", "10.0.0.8,GET,/login", "Preserve input order.", "Do not print the header."),
        ds,
        "\n".join(",".join(c[1:4]) for c in cols),
        "tail -n +2 requests.csv | cut -d, -f2-4",
        "`-f2-4` selects the contiguous field range from column 2 through column 4.",
    ))

    _add(ex, make(
        "expanded.requests.cut_complement",
        "Exclude one CSV column",
        'From "requests.csv", skip the header and print every column except TS using cut complement mode.',
        "focused",
        ["tail", "cut"],
        [skill("cut.complement"), skill("cut.fields", "reinforcement"), skill("tail.from_line", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("CSV WITHOUT TS", "10.0.0.8,GET,/login,200,512,30", "Preserve input order.", "Do not print the header."),
        ds,
        "\n".join(",".join(c[1:]) for c in cols),
        "tail -n +2 requests.csv | cut -d, --complement -f1",
        "`--complement` emits every delimited field except the selected field list.",
    ))

    return ex


def _users_exercises(ds: Dataset) -> list[Exercise]:
    ex: list[Exercise] = []

    groups = ["alpha", "alpha", "beta", "delta", "gamma", "gamma", "gamma", "omega"]
    gds = _with_files(ds, **{"groups.txt": _line_text(groups)})
    _add(ex, make(
        "expanded.users.uniq_duplicates",
        "Keep only repeated groups",
        'From already-grouped "groups.txt", print one copy of values that occur more than once.',
        "focused",
        ["uniq"],
        [skill("uniq.duplicates_only"), skill("uniq.basic", "reinforcement")],
        output("ONE VALUE PER LINE", "alpha\ngamma", "Input is already grouped."),
        gds,
        "alpha\ngamma",
        "uniq -d groups.txt",
        "`uniq -d` prints one representative for each adjacent group with more than one line.",
    ))
    _add(ex, make(
        "expanded.users.uniq_unique_only",
        "Keep only non-repeated groups",
        'From already-grouped "groups.txt", print values that occur exactly once.',
        "focused",
        ["uniq"],
        [skill("uniq.unique_only"), skill("uniq.basic", "reinforcement")],
        output("ONE VALUE PER LINE", "beta\ndelta\nomega", "Input is already grouped."),
        gds,
        "beta\ndelta\nomega",
        "uniq -u groups.txt",
        "`uniq -u` removes every repeated group entirely and keeps only groups of size one.",
    ))

    mixed = ["ALPHA", "alpha", "Beta", "BETA", "gamma"]
    mds = _with_files(ds, **{"mixed_case.txt": _line_text(mixed)})
    _add(ex, make(
        "expanded.users.uniq_ignore_case",
        "Collapse adjacent values ignoring case",
        'From "mixed_case.txt", collapse adjacent duplicates case-insensitively, preserving the first spelling in each group.',
        "focused",
        ["uniq"],
        [skill("uniq.ignore_case"), skill("uniq.basic", "reinforcement")],
        output("ONE REPRESENTATIVE PER GROUP", "ALPHA\nBeta\ngamma", "Preserve the first spelling of each adjacent group."),
        mds,
        "ALPHA\nBeta\ngamma",
        "uniq -i mixed_case.txt",
        "`-i` changes equality testing but `uniq` still emits the first line from each adjacent group.",
    ))

    skip = ["001 ERROR", "002 ERROR", "003 WARN", "004 WARN", "005 INFO"]
    sds = _with_files(ds, **{"timestamped.txt": _line_text(skip)})
    _add(ex, make(
        "expanded.users.uniq_skip_fields",
        "Ignore a leading field when comparing",
        'From "timestamped.txt", collapse adjacent records by their second field, ignoring the first field.',
        "focused",
        ["uniq"],
        [skill("uniq.skip_fields"), skill("uniq.basic", "reinforcement")],
        output("REPRESENTATIVE RECORDS", "001 ERROR\n003 WARN\n005 INFO", "Preserve the first record from each adjacent group."),
        sds,
        "001 ERROR\n003 WARN\n005 INFO",
        "uniq -f 1 timestamped.txt",
        "`-f 1` skips the first whitespace field when deciding whether adjacent lines are duplicates.",
    ))

    stable = ["beta 3", "alpha 9", "beta 1", "alpha 2", "beta 8", "alpha 7"]
    stds = _with_files(ds, **{"stable.txt": _line_text(stable)})
    stable_expected = "\n".join(sorted(stable, key=lambda line: line.split()[0]))
    _add(ex, make(
        "expanded.users.sort_stable",
        "Preserve tie order while sorting",
        'Sort "stable.txt" by field 1 while preserving the original relative order of rows whose field 1 is equal.',
        "focused",
        ["sort"],
        [skill("sort.stable"), skill("sort.keys", "reinforcement")],
        output("SORTED RECORDS", "alpha 9\nalpha 2\n...", "Equal field-1 keys must preserve input order."),
        stds,
        stable_expected,
        "sort -s -k1,1 stable.txt",
        "`-s` prevents sort's fallback whole-line comparison from reordering records whose selected key is equal.",
    ))

    return ex


def _jsonl_exercises(ds: Dataset) -> list[Exercise]:
    ex: list[Exercise] = []
    records = ds.records
    filename = ds.primary_file or "events.jsonl"

    matches = [r for r in records if r.get("level") == "ERROR" or int(r.get("status", 0)) >= 500]
    _add(ex, make(
        "expanded.jsonl.jq_boolean",
        "Combine JSON conditions",
        f'From "{filename}", print SERVICE where LEVEL is `ERROR` OR STATUS is at least 500.',
        "focused",
        ["jq"],
        [skill("jq.boolean"), skill("jq.select", "reinforcement"), skill("jq.field", "reinforcement"), skill("jq.raw", "reinforcement")],
        output("SERVICE", "api", "One service per matching object.", "Preserve input order.", "Print raw strings."),
        ds,
        "\n".join(str(r["service"]) for r in matches),
        f"jq -r 'select((.level == \"ERROR\") or (.status >= 500)) | .service' {filename}",
        "jq uses the word `or` between complete boolean expressions inside `select(...)`.",
    ))

    _add(ex, make(
        "expanded.jsonl.jq_multi_field",
        "Emit multiple JSON fields",
        f'From "{filename}", print SERVICE and USER as tab-separated fields for every object.',
        "focused",
        ["jq"],
        [skill("jq.multi_field"), skill("jq.arrays", "reinforcement"), skill("jq.field", "reinforcement"), skill("jq.raw", "reinforcement")],
        output("SERVICE<TAB>USER", "api\talice", "One output row per JSON object.", "Preserve input order."),
        ds,
        "\n".join(f'{r["service"]}\t{r["user"]}' for r in records),
        f"jq -r '[.service, .user] | @tsv' {filename}",
        "An array can collect several fields and `@tsv` renders those values as one tab-separated record.",
    ))

    array_obj = {"hosts": ["web-01", "db-01", "worker-01", "cache-01"]}
    ads = _with_files(ds, **{"arrays.json": json.dumps(array_obj) + "\n"})
    _add(ex, make(
        "expanded.jsonl.jq_arrays",
        "Index a JSON array",
        'From "arrays.json", print the second element of the `hosts` array as raw text.',
        "focused",
        ["jq"],
        [skill("jq.arrays"), skill("jq.field", "reinforcement"), skill("jq.raw", "reinforcement")],
        output("ONE HOST", "db-01", "Arrays are zero-indexed."),
        ads,
        "db-01",
        "jq -r '.hosts[1]' arrays.json",
        "`.hosts` selects the array and `[1]` selects its second element because jq array indexes start at zero.",
    ))

    _add(ex, make(
        "expanded.jsonl.jq_length",
        "Count JSONL objects with jq length",
        f'Collect all objects from "{filename}" into an array and print its length using jq only.',
        "focused",
        ["jq"],
        [skill("jq.length"), skill("jq.arrays", "reinforcement")],
        output("ONE NUMBER", "42", "Print exactly one number."),
        ds,
        str(len(records)),
        f"jq -s 'length' {filename}",
        "`-s` slurps the JSONL stream into one array; `length` then returns the number of elements.",
    ))

    _add(ex, make(
        "expanded.jsonl.jq_map",
        "Map over JSON objects",
        f'Using `map()`, print SERVICE from every object in "{filename}" as raw text, preserving input order.',
        "focused",
        ["jq"],
        [skill("jq.map"), skill("jq.arrays", "reinforcement"), skill("jq.raw", "reinforcement")],
        output("SERVICE", "api", "One service per line.", "Preserve input order."),
        ds,
        "\n".join(str(r["service"]) for r in records),
        f"jq -s -r 'map(.service)[]' {filename}",
        "After slurping into an array, `map(.service)` builds an array of services and `[]` streams its elements.",
    ))

    sorted_records = sorted(records, key=lambda r: (r["duration_ms"], json.dumps(r, sort_keys=True)))
    _add(ex, make(
        "expanded.jsonl.jq_sort_by",
        "Sort JSON objects by a field",
        f'From "{filename}", print DURATION_MS values sorted ascending using jq `sort_by()`.',
        "focused",
        ["jq"],
        [skill("jq.sort_by"), skill("jq.arrays", "reinforcement")],
        output("DURATION_MS", "12\n45\n93", "One number per line.", "Ascending order."),
        ds,
        "\n".join(str(r["duration_ms"]) for r in sorted_records),
        f"jq -s -r 'sort_by(.duration_ms)[] | .duration_ms' {filename}",
        "`sort_by(.duration_ms)` orders the slurped array by that numeric property.",
    ))

    counts = Counter(str(r["service"]) for r in records)
    group_expected = "\n".join(f"{counts[name]} {name}" for name in sorted(counts))
    _add(ex, make(
        "expanded.jsonl.jq_group_by",
        "Group JSON objects by a field",
        f'Group objects from "{filename}" by SERVICE with jq and print `COUNT SERVICE`, ordered by service name.',
        "focused",
        ["jq"],
        [skill("jq.group_by"), skill("jq.arrays", "reinforcement")],
        output("COUNT SERVICE", "7 api", "One group per line.", "Service names in normal text order."),
        ds,
        group_expected,
        f"jq -s -r 'group_by(.service)[] | \"\\(length) \\(.[0].service)\"' {filename}",
        "Each `group_by(.service)` result is an array. `length` gives its count and `.[0].service` gives the shared key.",
    ))

    unique_services = sorted({str(r["service"]) for r in records})
    _add(ex, make(
        "expanded.jsonl.jq_unique_by",
        "Deduplicate JSON objects by a field",
        f'From "{filename}", print one SERVICE for each distinct service using jq `unique_by()`.',
        "focused",
        ["jq"],
        [skill("jq.unique_by"), skill("jq.arrays", "reinforcement"), skill("jq.raw", "reinforcement")],
        output("UNIQUE SERVICE", "api\nauth\nworker", "One service per line.", "Normal jq unique ordering."),
        ds,
        "\n".join(unique_services),
        f"jq -s -r 'unique_by(.service)[] | .service' {filename}",
        "`unique_by(.service)` keeps one object for each distinct service value.",
    ))

    max_duration = max(records, key=lambda r: r["duration_ms"])["duration_ms"]
    _add(ex, make(
        "expanded.jsonl.jq_max_by",
        "Select a maximum JSON object",
        f'From "{filename}", print the largest DURATION_MS using jq `max_by()`.',
        "focused",
        ["jq"],
        [skill("jq.minmax"), skill("jq.arrays", "reinforcement")],
        output("ONE NUMBER", "1800", "Print exactly one number."),
        ds,
        str(max_duration),
        f"jq -s -r 'max_by(.duration_ms).duration_ms' {filename}",
        "`max_by(.duration_ms)` selects the object with the greatest duration, then `.duration_ms` extracts its value.",
    ))

    nested_rows = [json.dumps({"meta": {"service": r["service"], "user": r["user"]}, "metrics": {"duration_ms": r["duration_ms"]}}, separators=(",", ":")) for r in records]
    nds = _with_files(ds, **{"nested.jsonl": _line_text(nested_rows)})
    _add(ex, make(
        "expanded.jsonl.jq_nested",
        "Traverse nested JSON",
        'From "nested.jsonl", print `meta.service` as raw text for every object.',
        "focused",
        ["jq"],
        [skill("jq.nested"), skill("jq.field", "reinforcement"), skill("jq.raw", "reinforcement")],
        output("SERVICE", "api", "One service per line.", "Preserve input order."),
        nds,
        "\n".join(str(r["service"]) for r in records),
        "jq -r '.meta.service' nested.jsonl",
        "Nested object traversal chains field selectors from the root: `.meta.service`.",
    ))

    compact = [json.dumps({"service": r["service"], "duration_ms": r["duration_ms"]}, separators=(",", ":")) for r in records]
    _add(ex, make(
        "expanded.jsonl.jq_construct",
        "Construct new JSON objects",
        f'From "{filename}", emit compact JSON objects containing only `service` and `duration_ms`.',
        "focused",
        ["jq"],
        [skill("jq.construct"), skill("jq.field", "reinforcement")],
        output("COMPACT JSON", '{"service":"api","duration_ms":42}', "One object per input object.", "Do not include other keys."),
        ds,
        "\n".join(compact),
        f"jq -c '{{service: .service, duration_ms: .duration_ms}}' {filename}",
        "jq object syntax builds a new object whose values are read from the original input object.",
    ))

    return ex


def build_expanded_exercises(ds: Dataset) -> list[Exercise]:
    """Extra curriculum templates for non-AWK tools.

    These templates deliberately reuse the existing dataset families so the
    adaptive system can teach a wider command vocabulary without reducing AWK's
    importance or adding another data-generation layer.
    """
    builders = {
        "words": _words_exercises,
        "auth": _auth_exercises,
        "config": _config_exercises,
        "filetree": _filetree_exercises,
        "requests_csv": _requests_exercises,
        "users": _users_exercises,
        "jsonl": _jsonl_exercises,
    }
    builder = builders.get(ds.kind)
    return builder(ds) if builder else []
