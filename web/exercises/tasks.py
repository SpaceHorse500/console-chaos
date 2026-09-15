from __future__ import annotations

import random
from collections import Counter
from typing import Callable

from .models import Dataset, Exercise, OutputSpec, SkillUse

Task = Callable[[Dataset], Exercise]


def skill(skill_id: str, role: str = "target") -> SkillUse:
    return SkillUse(skill_id=skill_id, role=role)


def output(label: str, example: str, *rules: str) -> OutputSpec:
    return OutputSpec(label=label, example=example, rules=list(rules))


def make(
    template_id: str,
    title: str,
    prompt: str,
    style: str,
    tools: list[str],
    skills: list[SkillUse],
    output_spec: OutputSpec,
    dataset: Dataset,
    expected: str,
    solution: str,
    explanation: str,
) -> Exercise:
    return Exercise(
        template_id=template_id,
        title=title,
        prompt=prompt,
        style=style,
        tools=tools,
        skills=skills,
        output=output_spec,
        dataset_kind=dataset.kind,
        files=dataset.files,
        expected=expected,
        solution=solution,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# words
# ---------------------------------------------------------------------------

def words_count_words(ds):
    return make(
        "words.count_words",
        "Count words",
        'Print only the number of words in "notes.txt".',
        "focused",
        ["wc"],
        [skill("wc.words"), skill("shell.redirection.input")],
        output("NUMBER", "42", "Print exactly one number.", "Do not print the filename."),
        ds,
        str(len(ds.records)),
        "wc -w < notes.txt",
        "`wc -w` counts words. `< notes.txt` redirects the file to standard input, so `wc` prints only the count instead of adding the filename.",
    )


def words_count_lines(ds):
    return make(
        "words.count_lines",
        "Count lines",
        'Print only the number of lines in "words.txt".',
        "focused",
        ["wc"],
        [skill("wc.lines"), skill("shell.redirection.input", "reinforcement")],
        output("NUMBER", "18", "Print exactly one number.", "Do not print the filename."),
        ds,
        str(len(ds.records)),
        "wc -l < words.txt",
        "`wc -l` counts lines. Input redirection keeps the output to the numeric count only.",
    )


def words_replace(ds):
    values = [r["value"] for r in ds.records]
    old = random.choice(values)
    new = random.choice([x for x in sorted(set(values)) if x != old])
    expected = "\n".join(new if x == old else x for x in values)
    return make(
        "words.replace_all",
        "Replace a word",
        f'Print "words.txt" with every `{old}` replaced by `{new}`. Do not modify the file.',
        "focused",
        ["sed"],
        [skill("sed.substitute", "prerequisite"), skill("sed.global")],
        output("TRANSFORMED TEXT", "server\nnetwork\nserver", "Keep the original line order.", "Do not edit the source file."),
        ds,
        expected,
        f"sed 's/{old}/{new}/g' words.txt",
        "`sed` is a stream editor. `s/OLD/NEW/g` substitutes every match on each line. Without `-i`, the original file is unchanged.",
    )



def words_replace_basic(ds):
    values = [r["value"] for r in ds.records]
    old = random.choice(values)
    new = random.choice([x for x in sorted(set(values)) if x != old])
    expected = "\n".join(new if x == old else x for x in values)
    return make(
        "words.replace_basic",
        "Basic text substitution",
        f'Print "words.txt" with `{old}` replaced by `{new}`. Each input line contains one word. Do not modify the file.',
        "focused",
        ["sed"],
        [skill("sed.substitute")],
        output("TRANSFORMED TEXT", "server\nnetwork\nserver", "Keep the original line order.", "Do not edit the source file."),
        ds,
        expected,
        f"sed 's/{old}/{new}/' words.txt",
        "`sed 's/OLD/NEW/'` replaces the first matching occurrence on each line. Here each line contains one word, so that is enough.",
    )


def words_first_three(ds):
    values = [r["value"] for r in ds.records]
    expected = "\n".join(values[:3])
    return make(
        "words.first_three",
        "First three lines",
        'From "words.txt", print only the first 3 lines.',
        "focused",
        ["head"],
        [skill("head.basic")],
        output("THREE LINES", "kernel\nnetwork\nserver", "Print exactly the first 3 input lines.", "Preserve order."),
        ds,
        expected,
        "head -n 3 words.txt",
        "`head -n 3` prints the first three lines of the file.",
    )


def words_last_three(ds):
    values = [r["value"] for r in ds.records]
    expected = "\n".join(values[-3:])
    return make(
        "words.last_three",
        "Last three lines",
        'From "words.txt", print only the last 3 lines.',
        "focused",
        ["tail"],
        [skill("tail.basic")],
        output("THREE LINES", "memory\ndaemon\ncloud", "Print exactly the last 3 input lines.", "Preserve order."),
        ds,
        expected,
        "tail -n 3 words.txt",
        "`tail -n 3` prints the final three lines of the file.",
    )


def words_numbers_desc(ds):
    numbers = [int(x) for x in ds.files["numbers.txt"].splitlines() if x.strip()]
    expected = "\n".join(str(x) for x in sorted(numbers, reverse=True))
    return make(
        "words.numbers_desc",
        "Sort numbers descending",
        'Print every number from "numbers.txt" from largest to smallest.',
        "focused",
        ["sort"],
        [skill("sort.numeric_reverse")],
        output("ONE NUMBER PER LINE", "942\n410\n37", "Sort numerically, not as text.", "Largest value first."),
        ds,
        expected,
        "sort -nr numbers.txt",
        "`sort -n` compares numeric values instead of text. `-r` reverses the result so the largest number comes first.",
    )


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

def users_unique(ds):
    expected = "\n".join(sorted({r["user"] for r in ds.records}))
    return make(
        "users.unique",
        "Unique users",
        'Print the unique usernames in "users.txt", sorted using normal text order.',
        "integration",
        ["sort", "uniq"],
        [skill("sort.basic"), skill("uniq.basic"), skill("shell.pipeline.basic", "reinforcement")],
        output("ONE USER PER LINE", "alice\nbob\nerin", "Remove duplicates.", "Sort using normal text order."),
        ds,
        expected,
        "sort users.txt | uniq",
        "`sort` puts identical usernames next to each other. `uniq` removes adjacent duplicates.",
    )


def users_count_adjacent(ds):
    counts = Counter(r["user"] for r in ds.records)
    expected = "\n".join(f"{counts[name]} {name}" for name in sorted(counts))
    return make(
        "users.uniq_count",
        "Count grouped usernames",
        '"users_sorted.txt" is already sorted. Print `COUNT USER` for each username in username order.',
        "focused",
        ["uniq", "awk"],
        [skill("uniq.count"), skill("awk.fields", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("COUNT USER", "4 alice\n7 bob\n2 carol", "One username per line.", "Keep username order."),
        ds,
        expected,
        "uniq -c users_sorted.txt | awk '{print $1, $2}'",
        "`uniq -c` prefixes each adjacent duplicate group with its count. The final awk removes the padding and prints `COUNT USER` cleanly.",
    )


def users_frequency(ds):
    counts = Counter(r["user"] for r in ds.records)
    ordered = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    expected = "\n".join(f"{count} {name}" for name, count in ordered)
    return make(
        "users.frequency",
        "User frequency table",
        'Print `COUNT USER` for each username, highest count first. Break ties using normal text order.',
        "integration",
        ["sort", "uniq", "awk"],
        [
            skill("uniq.count"),
            skill("sort.multiple_keys"),
            skill("awk.fields", "reinforcement"),
            skill("shell.pipeline.multi", "reinforcement"),
        ],
        output("COUNT USER", "9 alice\n5 bob\n2 erin", "One user per line.", "Highest count first.", "Break equal counts by username."),
        ds,
        expected,
        "sort users.txt | uniq -c | sort -k1,1nr -k2,2 | awk '{print $1, $2}'",
        "`uniq -c` counts adjacent duplicates. `sort -k1,1nr -k2,2` sorts count numerically descending and username as a tie-breaker. The final `awk` normalizes spacing.",
    )


def users_sort_basic(ds):
    expected = "\n".join(sorted(r["user"] for r in ds.records))
    return make(
        "users.sort_basic",
        "Sort usernames",
        'Print every line from "users.txt" sorted using normal text order. Keep duplicates.',
        "focused",
        ["sort"],
        [skill("sort.basic")],
        output("ONE USER PER LINE", "alice\nalice\nbob\nerin", "Keep duplicates.", "Use normal text order."),
        ds,
        expected,
        "sort users.txt",
        "Plain `sort` orders complete lines using normal text order. It does not remove duplicates.",
    )


def users_uniq_adjacent(ds):
    expected = "\n".join(sorted({r["user"] for r in ds.records}))
    return make(
        "users.uniq_adjacent",
        "Remove adjacent duplicate users",
        '"users_sorted.txt" is already sorted. Print each username only once.',
        "focused",
        ["uniq"],
        [skill("uniq.basic")],
        output("ONE USER PER LINE", "alice\nbob\ncarol", "The input is already grouped.", "Keep the existing order."),
        ds,
        expected,
        "uniq users_sorted.txt",
        "`uniq` removes adjacent duplicate lines. The file is pre-sorted so equal usernames are already next to one another.",
    )


def users_first_alphabetical(ds):
    first = sorted(r["user"] for r in ds.records)[0]
    return make(
        "users.first_alphabetical",
        "First username after sorting",
        'Print only the first username after sorting "users.txt" using normal text order.',
        "focused",
        ["sort", "head"],
        [skill("shell.pipeline.basic"), skill("sort.basic", "reinforcement"), skill("head.basic", "reinforcement")],
        output("ONE USER", "alice", "Print exactly one line."),
        ds,
        first,
        "sort users.txt | head -1",
        "The pipe sends sorted output directly into `head`. `head -1` keeps only the first line.",
    )


# ---------------------------------------------------------------------------
# requests.csv
# ---------------------------------------------------------------------------

def csv_awk_ip_column(ds):
    expected = "ip\n" + "\n".join(r["ip"] for r in ds.records)
    return make(
        "csv.awk_ip_column",
        "Read a CSV field with AWK",
        'From "requests.csv", print field 2 from every row, including the header.',
        "focused",
        ["awk"],
        [skill("awk.separator")],
        output("ONE FIELD PER INPUT ROW", "ip\n203.0.113.7\n198.51.100.4", "Include the header value.", "Preserve row order."),
        ds,
        expected,
        "awk -F, '{print $2}' requests.csv",
        "`-F,` tells awk that commas separate fields. `$2` is therefore the second CSV field.",
    )


def csv_awk_ips_without_header(ds):
    expected = "\n".join(r["ip"] for r in ds.records)
    return make(
        "csv.awk_skip_header",
        "Skip a CSV header with AWK",
        'From "requests.csv", print the IP field for data rows only. Do not print the header.',
        "focused",
        ["awk"],
        [skill("awk.nr_nf"), skill("awk.separator", "reinforcement")],
        output("ONE IP PER DATA ROW", "203.0.113.7\n198.51.100.4", "Do not print the header.", "Preserve data-row order."),
        ds,
        expected,
        "awk -F, 'NR>1 {print $2}' requests.csv",
        "`NR` is the current input row number. `NR>1` skips row 1, while `$2` prints the IP field.",
    )


def csv_cut_ips(ds):
    expected = "\n".join(r["ip"] for r in ds.records)
    return make(
        "csv.cut_ips",
        "Extract a CSV column with cut",
        'From "requests.csv", print the IP field for data rows only using `cut` for field extraction.',
        "focused",
        ["tail", "cut"],
        [skill("cut.fields"), skill("tail.basic", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("ONE IP PER DATA ROW", "203.0.113.7\n198.51.100.4", "Do not print the header.", "Preserve data-row order."),
        ds,
        expected,
        "tail -n +2 requests.csv | cut -d, -f2",
        "`tail -n +2` starts at line 2. `cut -d, -f2` uses comma as the delimiter and emits field 2.",
    )


def csv_status_ips(ds):
    target = random.choice([404, 500, 502])
    expected = "\n".join(r["ip"] for r in ds.records if r["status"] == target)
    return make(
        "csv.status_ips",
        "Extract IPs by HTTP status",
        f'From "requests.csv", print only IP addresses for rows with HTTP status {target}, preserving order.',
        "focused",
        ["awk"],
        [skill("awk.separator", "prerequisite"), skill("awk.nr_nf", "reinforcement"), skill("awk.conditions")],
        output("ONE IP PER MATCH", "203.0.113.7\n198.51.100.4", "Do not print the CSV header.", "Preserve matching-row order."),
        ds,
        expected,
        f"awk -F, 'NR>1 && $5 == {target} {{print $2}}' requests.csv",
        f"`-F,` uses comma as the separator. `NR>1` skips the header. `$5 == {target}` checks status and `$2` is the IP.",
    )


def csv_count_status(ds):
    target = random.choice([200, 404, 500])
    count = sum(1 for r in ds.records if r["status"] == target)
    return make(
        "csv.count_status",
        "Count HTTP responses",
        f'Print only the number of requests with status {target} in "requests.csv".',
        "focused",
        ["awk"],
        [skill("awk.conditions", "prerequisite"), skill("awk.variables_end")],
        output("NUMBER", "7", "Print exactly one number."),
        ds,
        str(count),
        f"awk -F, 'NR>1 && $5 == {target} {{c++}} END {{print c+0}}' requests.csv",
        "`c++` increments a counter for each match. `END` runs after all input has been read. `c+0` guarantees numeric zero if nothing matched.",
    )


def csv_slow_paths(ds):
    threshold = random.choice([300, 500, 800, 1000])
    expected = "\n".join(r["path"] for r in ds.records if r["duration_ms"] > threshold)
    return make(
        "csv.slow_paths",
        "Find slow HTTP requests",
        f'From "requests.csv", print the path for every request slower than {threshold} ms, preserving order.',
        "focused",
        ["awk"],
        [skill("awk.separator", "reinforcement"), skill("awk.conditions")],
        output("ONE PATH PER MATCH", "/api/users\n/login\n/api/orders", "Preserve matching-row order.", "Do not print the header."),
        ds,
        expected,
        f"awk -F, 'NR>1 && $7 > {threshold} {{print $4}}' requests.csv",
        "`$7` is `duration_ms` and `$4` is path. The condition keeps rows above the threshold.",
    )


def csv_top_failing_ip(ds):
    counts = Counter(r["ip"] for r in ds.records if r["status"] >= 500)
    winner = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
    expected = f"{winner[1]} {winner[0]}"
    return make(
        "csv.top_5xx_ip",
        "Incident: top 5xx client",
        'Find the IP with the most HTTP 5xx responses in "requests.csv". Break ties using normal text order.',
        "challenge",
        ["awk", "sort", "uniq", "head"],
        [
            skill("awk.conditions", "reinforcement"),
            skill("uniq.count", "reinforcement"),
            skill("sort.multiple_keys"),
            skill("head.basic", "reinforcement"),
            skill("shell.pipeline.multi"),
        ],
        output("COUNT IP", "12 203.0.113.42", "Print exactly one line.", "Count first, then IP."),
        ds,
        expected,
        "awk -F, 'NR>1 && $5 >= 500 {print $2}' requests.csv | sort | uniq -c | sort -k1,1nr -k2,2 | head -1 | awk '{print $1, $2}'",
        "Extract 5xx client IPs, group and count them, rank by count descending with IP as the tie-breaker, keep the winner, then normalize spacing.",
    )


def csv_unique_paths(ds):
    expected = "\n".join(sorted({r["path"] for r in ds.records}))
    return make(
        "csv.unique_paths",
        "Unique HTTP paths",
        'Print every unique path from "requests.csv", sorted using normal text order.',
        "integration",
        ["tail", "cut", "sort"],
        [skill("tail.basic"), skill("cut.fields"), skill("sort.unique"), skill("shell.pipeline.multi", "reinforcement")],
        output("ONE PATH PER LINE", "/\n/api/orders\n/login", "Do not print the header.", "Remove duplicates.", "Sort using normal text order."),
        ds,
        expected,
        "tail -n +2 requests.csv | cut -d, -f4 | sort -u",
        "`tail -n +2` skips the header. `cut -d, -f4` extracts CSV field 4. `sort -u` sorts and removes duplicates.",
    )


def csv_average_duration(ds):
    avg = sum(r["duration_ms"] for r in ds.records) / len(ds.records)
    expected = f"{avg:.2f}"
    return make(
        "csv.average_duration",
        "Average request duration",
        'From "requests.csv", print the average `duration_ms` across data rows, rounded to exactly 2 decimal places.',
        "focused",
        ["awk"],
        [skill("awk.separator", "reinforcement"), skill("awk.variables_end")],
        output("DECIMAL NUMBER", "437.25", "Print exactly one line.", "Always show exactly 2 digits after the decimal point."),
        ds,
        expected,
        "awk -F, 'NR>1 {sum+=$7; n++} END {printf \"%.2f\\n\", sum/n}' requests.csv",
        "The body accumulates total duration and row count. `END` computes the average after input ends. `printf` controls the two-decimal output format.",
    )


def csv_status_frequency_awk(ds):
    counts = Counter(str(r["status"]) for r in ds.records)
    expected = "\n".join(f"{status} {counts[status]}" for status in sorted(counts, key=int))
    return make(
        "csv.status_frequency_awk",
        "Count statuses inside AWK",
        'From "requests.csv", print `STATUS COUNT` for every HTTP status, sorted numerically by status. Perform the counting inside AWK.',
        "focused",
        ["awk", "sort"],
        [skill("awk.assoc_arrays"), skill("awk.aggregation"), skill("sort.keys", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("STATUS COUNT", "200 14\n404 3\n500 2", "One status per line.", "Sort numerically by status."),
        ds,
        expected,
        "awk -F, 'NR>1 {count[$5]++} END {for (s in count) print s, count[s]}' requests.csv | sort -k1,1n",
        "`count[$5]++` uses the status as an associative-array key. `END` loops over the accumulated groups. The final sort makes the otherwise unordered array output deterministic.",
    )


# ---------------------------------------------------------------------------
# nginx
# ---------------------------------------------------------------------------

def nginx_client_ips(ds):
    expected = "\n".join(r["ip"] for r in ds.records)
    return make(
        "nginx.client_ips",
        "Print nginx client IPs",
        'From "access.log", print only the client IP from every line, preserving order.',
        "focused",
        ["awk"],
        [skill("awk.fields")],
        output("ONE IP PER INPUT LINE", "203.0.113.7\n198.51.100.4\n203.0.113.7", "Preserve input order.", "Keep duplicates."),
        ds,
        expected,
        "awk '{print $1}' access.log",
        "By default awk splits on whitespace. The client IP is field `$1`, so printing `$1` extracts it from every line.",
    )


def nginx_status_lines(ds):
    target = random.choice([404, 500, 502])
    source_lines = ds.files["access.log"].splitlines()
    expected = "\n".join(line for line, r in zip(source_lines, ds.records) if r["status"] == target)
    return make(
        "nginx.status_lines",
        "Filter nginx status",
        f'Print complete lines from "access.log" whose HTTP status is {target}.',
        "focused",
        ["awk"],
        [skill("awk.fields", "prerequisite"), skill("awk.conditions")],
        output("COMPLETE MATCHING LINES", '203.0.113.7 - - [14/Sep/2026:01:15:00 +0000] "GET /api HTTP/1.1" 500 421 33ms', "Do not extract individual fields.", "Preserve input order."),
        ds,
        expected,
        f"awk '$9 == {target}' access.log",
        "In this nginx format the status is field 9. An awk condition with no explicit action prints matching complete lines.",
    )


def nginx_unique_ips(ds):
    expected = "\n".join(sorted({r["ip"] for r in ds.records}))
    return make(
        "nginx.unique_ips",
        "Unique nginx clients",
        'Print unique client IP addresses in "access.log", sorted using normal text order.',
        "integration",
        ["awk", "sort"],
        [skill("awk.fields", "reinforcement"), skill("sort.unique"), skill("shell.pipeline.basic", "reinforcement")],
        output("ONE IP PER LINE", "10.0.0.12\n10.0.0.4\n203.0.113.7", "Remove duplicates.", "Use normal text/lexicographical sorting, not numeric IP sorting."),
        ds,
        expected,
        "awk '{print $1}' access.log | sort -u",
        "The client IP is field 1. `sort -u` performs normal text sorting and removes duplicates.",
    )


def nginx_top_ip(ds):
    counts = Counter(r["ip"] for r in ds.records)
    winner = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
    return make(
        "nginx.top_ip",
        "Most active nginx client",
        'Print the most frequent client from "access.log" as `COUNT IP`. Break ties using normal text order.',
        "integration",
        ["awk", "sort", "uniq", "head"],
        [skill("uniq.count"), skill("sort.multiple_keys"), skill("head.basic", "reinforcement"), skill("shell.pipeline.multi")],
        output("COUNT IP", "17 203.0.113.7", "Print exactly one line.", "Count first, then IP."),
        ds,
        f"{winner[1]} {winner[0]}",
        "awk '{print $1}' access.log | sort | uniq -c | sort -k1,1nr -k2,2 | head -1 | awk '{print $1, $2}'",
        "Extract client IPs, count adjacent duplicates, rank by count descending and IP as a tie-breaker, then keep the first result.",
    )


def nginx_slow_paths(ds):
    threshold = random.choice([400, 700, 1000])
    expected = "\n".join(r["path"] for r in ds.records if r["duration_ms"] > threshold)
    return make(
        "nginx.slow_paths",
        "Slow nginx paths",
        f'Print the path for every request in "access.log" slower than {threshold} ms, preserving order.',
        "focused",
        ["awk"],
        [skill("awk.fields", "prerequisite"), skill("awk.conditions")],
        output("ONE PATH PER MATCH", "/api/users\n/login", "Preserve matching-row order."),
        ds,
        expected,
        f"awk '$11+0 > {threshold} {{print $7}}' access.log",
        "The path is field 7. Duration is field 11 and looks like `812ms`; adding `+0` makes awk use its numeric prefix.",
    )


# ---------------------------------------------------------------------------
# auth.log
# ---------------------------------------------------------------------------

def auth_failed_lines(ds):
    expected = "\n".join(r["line"] for r in ds.records if r["outcome"] == "failed")
    return make(
        "auth.failed_lines",
        "SSH failures",
        'Print every failed SSH authentication line from "auth.log".',
        "focused",
        ["grep"],
        [skill("grep.literal")],
        output("COMPLETE MATCHING LINES", "Sep 14 01:03:02 server sshd[1234]: Failed password for root from 203.0.113.7 port 44220 ssh2", "Print complete lines.", "Preserve input order."),
        ds,
        expected,
        "grep 'Failed password' auth.log",
        "`grep` prints complete input lines containing the supplied text pattern.",
    )


def auth_failed_lines_awk(ds):
    expected = "\n".join(r["line"] for r in ds.records if r["outcome"] == "failed")
    return make(
        "auth.failed_lines_awk",
        "Match log lines with an AWK regex",
        'Using AWK, print every line in "auth.log" containing `Failed password`.',
        "focused",
        ["awk"],
        [skill("awk.regex")],
        output("COMPLETE MATCHING LINES", "Sep 14 01:03:02 server sshd[1234]: Failed password for root from 203.0.113.7 port 44220 ssh2", "Print complete matching lines.", "Preserve input order."),
        ds,
        expected,
        "awk '/Failed password/' auth.log",
        "In awk, `/Failed password/` is a pattern applied to `$0`, the entire current line. With no explicit action, matching lines are printed.",
    )


def auth_failed_ips(ds):
    expected = "\n".join(r["ip"] for r in ds.records if r["outcome"] == "failed")
    return make(
        "auth.failed_ips",
        "Extract failed SSH source IPs",
        'Print only the source IP for every failed SSH authentication in "auth.log", preserving order.',
        "focused",
        ["awk"],
        [
            skill("awk.regex", "prerequisite"),
            skill("awk.loops"),
            skill("awk.dynamic_fields"),
        ],
        output("ONE IP PER FAILED LOGIN", "203.0.113.7\n198.51.100.4", "Preserve failed-login order.", "Keep duplicates."),
        ds,
        expected,
        r'''awk '/Failed password/ {for (i=1; i<=NF; i++) if ($i=="from") print $(i+1)}' auth.log''',
        "Some rows contain `invalid user`, so fixed field numbers are unreliable. Loop through fields, find the literal `from`, and print the following field dynamically.",
    )


def auth_top_failed_ip(ds):
    counts = Counter(r["ip"] for r in ds.records if r["outcome"] == "failed")
    winner = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
    return make(
        "auth.top_failed_ip",
        "Incident: SSH brute-force source",
        'Find the IP with the most failed SSH logins in "auth.log". Break ties using normal text order.',
        "challenge",
        ["awk", "sort", "uniq", "head"],
        [
            skill("awk.dynamic_fields", "reinforcement"),
            skill("uniq.count", "reinforcement"),
            skill("sort.multiple_keys"),
            skill("shell.pipeline.multi"),
        ],
        output("COUNT IP", "20 203.0.113.42", "Print exactly one line.", "Count first, then IP."),
        ds,
        f"{winner[1]} {winner[0]}",
        r'''awk '/Failed password/ {for (i=1; i<=NF; i++) if ($i=="from") print $(i+1)}' auth.log | sort | uniq -c | sort -k1,1nr -k2,2 | head -1 | awk '{print $1, $2}' ''',
        "Extract the field following `from`, group and count IPs, rank them by count descending with a deterministic tie-breaker, then keep the first result.",
    )


# ---------------------------------------------------------------------------
# app key=value
# ---------------------------------------------------------------------------

def app_error_lines(ds):
    source_lines = ds.files["app.log"].splitlines()
    expected = "\n".join(line for line, r in zip(source_lines, ds.records) if r["level"] == "ERROR")
    return make(
        "app.error_lines",
        "Application errors",
        'Print complete ERROR lines from "app.log".',
        "focused",
        ["grep"],
        [skill("grep.literal")],
        output("COMPLETE MATCHING LINES", "2026-09-14T01:30:00 level=ERROR service=api user=alice duration_ms=420 status=failed", "Print complete lines.", "Preserve input order."),
        ds,
        expected,
        "grep 'level=ERROR' app.log",
        "`grep` selects lines containing the exact key/value pair `level=ERROR`.",
    )


def app_error_services(ds):
    expected = "\n".join(r["service"] for r in ds.records if r["level"] == "ERROR")
    return make(
        "app.error_services",
        "Services producing errors",
        'Print only the service name for each ERROR entry in "app.log", preserving order.',
        "focused",
        ["awk"],
        [skill("awk.regex", "prerequisite"), skill("awk.loops", "reinforcement"), skill("awk.split")],
        output("ONE SERVICE PER ERROR", "api\nbilling\napi", "Preserve matching-row order.", "Do not print `service=`."),
        ds,
        expected,
        r'''awk '/level=ERROR/ {for(i=1;i<=NF;i++) if($i~/^service=/){split($i,a,"="); print a[2]}}' app.log''',
        "The regex selects ERROR lines. The loop finds the `service=` field. `split` separates key and value; `a[2]` is the service name.",
    )


def app_slow_services(ds):
    threshold = random.choice([400, 700, 1000])
    expected = "\n".join(r["service"] for r in ds.records if r["duration_ms"] > threshold)
    solution = rf'''awk '{{svc="";d=0;for(i=1;i<=NF;i++){{if($i~/^service=/){{split($i,a,"=");svc=a[2]}};if($i~/^duration_ms=/){{split($i,b,"=");d=b[2]}}}};if(d>{threshold})print svc}}' app.log'''
    return make(
        "app.slow_services",
        "Slow application events",
        f'Print the service name for entries in "app.log" with duration_ms greater than {threshold}, preserving order.',
        "integration",
        ["awk"],
        [skill("awk.loops", "reinforcement"), skill("awk.split"), skill("awk.conditions", "reinforcement")],
        output("ONE SERVICE PER MATCH", "search\napi\nworker", "Preserve matching-row order."),
        ds,
        expected,
        solution,
        "Scan each key=value field, extract `service` and `duration_ms`, then print the service when the parsed duration passes the threshold.",
    )


# ---------------------------------------------------------------------------
# JSONL
# ---------------------------------------------------------------------------

def json_services(ds):
    expected = "\n".join(r["service"] for r in ds.records)
    return make(
        "json.services",
        "Extract JSON service names",
        'From "events.jsonl", print the `service` value from every JSON object.',
        "focused",
        ["jq"],
        [skill("jq.field"), skill("jq.raw")],
        output("ONE SERVICE PER JSON OBJECT", "api\nworker\nsearch", "Preserve object order.", "Print raw strings without quotes."),
        ds,
        expected,
        r'''jq -r '.service' events.jsonl''',
        "`.service` extracts the field. `-r` prints string values without JSON quotation marks.",
    )


def json_errors(ds):
    expected = "\n".join(r["service"] for r in ds.records if r["level"] == "ERROR")
    return make(
        "json.error_services",
        "JSON error services",
        'From "events.jsonl", print the service value for every object whose level is ERROR.',
        "focused",
        ["jq"],
        [skill("jq.field", "prerequisite"), skill("jq.raw", "reinforcement"), skill("jq.select")],
        output("ONE SERVICE PER MATCH", "api\nbilling", "Preserve object order.", "Print raw strings without quotes."),
        ds,
        expected,
        r'''jq -r 'select(.level == "ERROR") | .service' events.jsonl''',
        "`select(...)` keeps matching JSON objects. `.service` extracts that field. `-r` prints raw strings without JSON quotes.",
    )


def json_slow(ds):
    threshold = random.choice([500, 800, 1000])
    expected = "\n".join(r["service"] for r in ds.records if r["duration_ms"] > threshold)
    return make(
        "json.slow_services",
        "Slow JSON events",
        f'From "events.jsonl", print service names for objects with duration_ms > {threshold}, preserving order.',
        "focused",
        ["jq"],
        [skill("jq.select"), skill("jq.raw", "reinforcement")],
        output("ONE SERVICE PER MATCH", "api\nsearch\nworker", "Preserve object order.", "Print raw strings without quotes."),
        ds,
        expected,
        rf'''jq -r 'select(.duration_ms > {threshold}) | .service' events.jsonl''',
        "`select(.duration_ms > N)` filters numerically and `.service` extracts the requested field.",
    )


def json_count_500(ds):
    count = sum(1 for r in ds.records if r["status"] == 500)
    return make(
        "json.count_500",
        "Count JSON status values",
        'Print only the number of objects in "events.jsonl" whose status is 500.',
        "integration",
        ["jq", "wc"],
        [skill("jq.select", "reinforcement"), skill("wc.lines"), skill("shell.pipeline.basic")],
        output("NUMBER", "6", "Print exactly one number."),
        ds,
        str(count),
        r'''jq -r 'select(.status == 500) | .status' events.jsonl | wc -l''',
        "`jq` emits one line for every matching object. `wc -l` counts those output lines.",
    )


# ---------------------------------------------------------------------------
# simulated ps
# ---------------------------------------------------------------------------


def ps_sort_by_cpu(ds):
    source_rows = ds.files["processes.txt"].splitlines()[1:]
    ordered = sorted(
        zip(ds.records, source_rows),
        key=lambda pair: -pair[0]["cpu"],
    )
    expected = "\n".join(row for _, row in ordered)
    return make(
        "ps.sort_by_cpu",
        "Sort processes by CPU",
        'From "processes.txt", print the data rows sorted by %CPU from highest to lowest. Do not print the header. Preserve original order when CPU values tie.',
        "focused",
        ["tail", "sort"],
        [skill("tail.basic", "reinforcement"), skill("sort.keys"), skill("sort.numeric_reverse")],
        output("COMPLETE PROCESS ROWS", "app 4127 87.4 4.1 /usr/bin/python3 api.py\nroot 1220 33.8 1.2 /usr/sbin/nginx", "Do not print the header.", "Highest CPU first.", "Preserve original order for equal CPU values."),
        ds,
        expected,
        "tail -n +2 processes.txt | sort -s -k3,3nr",
        "`-k3,3` selects only the CPU field as the sort key. `n` makes it numeric, `r` reverses it, and `-s` keeps original order when keys compare equal.",
    )


def ps_sort_cpu_then_pid(ds):
    source_rows = ds.files["processes.txt"].splitlines()[1:]
    ordered = sorted(
        zip(ds.records, source_rows),
        key=lambda pair: (-pair[0]["cpu"], pair[0]["pid"]),
    )
    expected = "\n".join(row for _, row in ordered)
    return make(
        "ps.sort_cpu_then_pid",
        "Sort with a tie-breaker",
        'From "processes.txt", print data rows sorted by %CPU highest first, then PID lowest first when CPU values tie. Do not print the header.',
        "focused",
        ["tail", "sort"],
        [skill("sort.multiple_keys"), skill("tail.basic", "reinforcement")],
        output("COMPLETE PROCESS ROWS", "app 4127 87.4 4.1 /usr/bin/python3 api.py\nroot 1220 33.8 1.2 /usr/sbin/nginx", "Do not print the header.", "CPU descending.", "PID ascending as the tie-breaker."),
        ds,
        expected,
        "tail -n +2 processes.txt | sort -k3,3nr -k2,2n",
        "The first key sorts CPU numerically in reverse. The second key sorts PID numerically ascending when CPU values compare equal.",
    )


def ps_top_cpu(ds):
    winner = sorted(ds.records, key=lambda r: (-r["cpu"], r["pid"]))[0]
    return make(
        "ps.top_cpu",
        "Top CPU process",
        'From "processes.txt", print `PID %CPU` for the process using the most CPU.',
        "integration",
        ["tail", "sort", "head", "awk"],
        [skill("tail.basic", "reinforcement"), skill("sort.multiple_keys"), skill("head.basic", "reinforcement"), skill("awk.fields", "reinforcement"), skill("shell.pipeline.multi")],
        output("PID %CPU", "4127 87.4", "Print exactly one line.", "PID first, CPU second."),
        ds,
        f'{winner["pid"]} {winner["cpu"]:.1f}',
        "tail -n +2 processes.txt | sort -k3,3nr -k2,2n | head -1 | awk '{print $2, $3}'",
        "Skip the header, sort CPU numerically descending with PID as a tie-breaker, keep the first row, then print PID and CPU.",
    )


def ps_over_cpu(ds):
    threshold = random.choice([25, 40, 60])
    expected = "\n".join(str(r["pid"]) for r in ds.records if r["cpu"] > threshold)
    return make(
        "ps.over_cpu",
        "Processes above CPU threshold",
        f'Print only PIDs from "processes.txt" whose %CPU is greater than {threshold}, preserving file order.',
        "focused",
        ["awk"],
        [skill("awk.nr_nf", "reinforcement"), skill("awk.conditions")],
        output("ONE PID PER MATCH", "1024\n1887\n2410", "Do not print the header.", "Preserve file order."),
        ds,
        expected,
        f"awk 'NR>1 && $3 > {threshold} {{print $2}}' processes.txt",
        "`NR>1` skips the header, `$3` is CPU and `$2` is PID.",
    )


# ---------------------------------------------------------------------------
# simulated df
# ---------------------------------------------------------------------------

def df_high_usage(ds):
    threshold = random.choice([70, 80, 85])
    expected = "\n".join(r["mount"] for r in ds.records if r["percent"] > threshold)
    return make(
        "df.high_usage",
        "High disk usage",
        f'From "df.txt", print mount points whose Use% is greater than {threshold}%, preserving order.',
        "focused",
        ["awk"],
        [skill("awk.conditions", "reinforcement"), skill("awk.substitution")],
        output("ONE MOUNT PER MATCH", "/var\n/data", "Do not print the header.", "Preserve file order."),
        ds,
        expected,
        f'''awk 'NR>1 {{p=$5; sub(/%/,"",p); if (p > {threshold}) print $6}}' df.txt''',
        "`$5` contains values such as `87%`. `sub` removes `%` from a copy so it can be compared numerically; `$6` is the mount point.",
    )



def df_usage_percentages(ds):
    expected = "\n".join(
        f'{r["percent"]}%'
        for r in sorted(ds.records, key=lambda r: -r["percent"])
    )
    return make(
        "df.usage_percentages",
        "Sort disk usage percentages",
        'From "df.txt", print only the Use% values for data rows, highest percentage first.',
        "integration",
        ["tail", "awk", "sort"],
        [skill("tail.basic", "reinforcement"), skill("awk.fields", "reinforcement"), skill("sort.numeric_reverse"), skill("shell.pipeline.multi", "reinforcement")],
        output("ONE Use% VALUE PER LINE", "93%\n81%\n42%", "Do not print the header.", "Highest percentage first.", "Keep the `%` sign."),
        ds,
        expected,
        "tail -n +2 df.txt | awk '{print $5}' | sort -nr",
        "Extract the Use% field, then `sort -n` compares numeric prefixes and `-r` reverses the order so the largest percentage comes first.",
    )


def df_most_used(ds):
    winner = sorted(ds.records, key=lambda r: (-r["percent"], r["mount"]))[0]
    return make(
        "df.most_used",
        "Most utilized filesystem",
        'From "df.txt", print `Use% MOUNT` for the most utilized filesystem.',
        "integration",
        ["tail", "sort", "head", "awk"],
        [skill("tail.basic", "reinforcement"), skill("sort.multiple_keys"), skill("head.basic", "reinforcement"), skill("awk.fields", "reinforcement"), skill("shell.pipeline.multi")],
        output("Use% MOUNT", "91% /var", "Print exactly one line.", "Keep the `%` sign."),
        ds,
        f'{winner["percent"]}% {winner["mount"]}',
        "tail -n +2 df.txt | sort -k5,5nr -k6,6 | head -1 | awk '{print $5, $6}'",
        "Sort Use% numerically in reverse, use mount point as a tie-breaker, keep the top row, then print Use% and mount.",
    )


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

def config_without_comments(ds):
    source = ds.files["service.conf"].splitlines()
    expected = "\n".join(line for line in source if not line.startswith("#"))
    return make(
        "config.no_comments",
        "Exclude comment lines",
        'Print "service.conf" without lines that start with `#`. Keep blank lines.',
        "focused",
        ["grep"],
        [skill("grep.invert"), skill("grep.literal", "reinforcement")],
        output("NON-COMMENT LINES", "\nPORT=8080\n\nWORKERS=4", "Keep blank lines.", "Preserve input order."),
        ds,
        expected,
        "grep -v '^#' service.conf",
        "`-v` inverts the match, so lines matching `^#` are excluded. `^` anchors the pattern at the start of the line.",
    )


def config_assignment_lines(ds):
    expected = "\n".join(r["line"] for r in ds.records)
    return make(
        "config.assignments",
        "Match configuration assignments",
        'Print only active `KEY=value` assignment lines from "service.conf" using a regular expression.',
        "focused",
        ["grep"],
        [skill("grep.regex")],
        output("ACTIVE ASSIGNMENT LINES", "PORT=8080\nWORKERS=4\nLOG_LEVEL=INFO", "Exclude comments and blank lines.", "Preserve input order."),
        ds,
        expected,
        "grep '^[A-Z_][A-Z_]*=' service.conf",
        "The regex is anchored at the start of the line and matches an uppercase key followed by `=`.",
    )


def config_active(ds):
    expected = "\n".join(r["line"] for r in ds.records)
    return make(
        "config.active",
        "Active configuration",
        'Print only active lines from "service.conf": exclude comments and blank lines.',
        "focused",
        ["grep"],
        [skill("grep.extended"), skill("grep.invert", "reinforcement"), skill("grep.regex", "reinforcement")],
        output("ACTIVE CONFIG LINES", "PORT=8080\nWORKERS=4\nLOG_LEVEL=INFO", "Keep original order.", "Exclude comments and blank lines."),
        ds,
        expected,
        r'''grep -vE '^[[:space:]]*(#|$)' service.conf''',
        "`-E` enables extended regex and `-v` inverts the match. The regex describes comment or blank lines, so those are excluded.",
    )


# ---------------------------------------------------------------------------
# file tree
# ---------------------------------------------------------------------------

def tree_find_logs(ds):
    expected = "\n".join(sorted(f'./{r["path"]}' for r in ds.records if r["path"].endswith(".log")))
    return make(
        "tree.find_logs",
        "Find log files",
        'From the exercise directory, print every `.log` file recursively, sorted using normal text order. Paths must begin with `./`.',
        "focused",
        ["find", "sort"],
        [skill("find.name_type"), skill("sort.basic", "reinforcement"), skill("shell.pipeline.basic", "reinforcement")],
        output("ONE RELATIVE PATH PER LINE", "./logs/api.log\n./logs/nginx/access.log", "Paths begin with `./`.", "Sort using normal text order."),
        ds,
        expected,
        "find . -type f -name '*.log' | sort",
        "`find .` searches recursively. `-type f` keeps regular files. `-name '*.log'` filters names. Quotes prevent the shell from expanding the wildcard before `find` receives it.",
    )


TASKS_BY_KIND: dict[str, list[Task]] = {
    "words": [words_count_words, words_count_lines, words_first_three, words_last_three, words_numbers_desc, words_replace_basic, words_replace],
    "users": [users_sort_basic, users_uniq_adjacent, users_count_adjacent, users_first_alphabetical, users_unique, users_frequency],
    "requests_csv": [
        csv_awk_ip_column,
        csv_awk_ips_without_header,
        csv_cut_ips,
        csv_status_ips,
        csv_count_status,
        csv_slow_paths,
        csv_top_failing_ip,
        csv_unique_paths,
        csv_average_duration,
        csv_status_frequency_awk,
    ],
    "nginx": [nginx_client_ips, nginx_status_lines, nginx_unique_ips, nginx_top_ip, nginx_slow_paths],
    "auth": [auth_failed_lines, auth_failed_lines_awk, auth_failed_ips, auth_top_failed_ip],
    "app_kv": [app_error_lines, app_error_services, app_slow_services],
    "jsonl": [json_services, json_errors, json_slow, json_count_500],
    "ps": [ps_sort_by_cpu, ps_sort_cpu_then_pid, ps_top_cpu, ps_over_cpu],
    "df": [df_high_usage, df_usage_percentages, df_most_used],
    "config": [config_without_comments, config_assignment_lines, config_active],
    "filetree": [tree_find_logs],
}
