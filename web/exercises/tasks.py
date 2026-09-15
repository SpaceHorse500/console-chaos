from __future__ import annotations

import random
from collections import Counter
from typing import Callable

from .models import Dataset, Exercise

Task = Callable[[Dataset], Exercise]


def make(title, prompt, difficulty, tools, dataset, expected, solution, explanation) -> Exercise:
    return Exercise(title, prompt, difficulty, tools, dataset.kind, dataset.files, expected, solution, explanation)


# words

def words_count_words(ds):
    return make(
        "Count words",
        'Print only the number of words in "notes.txt".',
        1, ["wc"], ds, str(len(ds.records)),
        "wc -w < notes.txt",
        "`wc` counts text. `-w` counts words. `< notes.txt` redirects the file to standard input, so only the number is printed."
    )


def words_count_lines(ds):
    return make(
        "Count lines",
        'Print only the number of lines in "words.txt".',
        1, ["wc"], ds, str(len(ds.records)),
        "wc -l < words.txt",
        "`wc -l` counts lines. Input redirection avoids printing the filename."
    )


def words_replace(ds):
    values = [r["value"] for r in ds.records]
    old = random.choice(values)
    new = random.choice([x for x in sorted(set(values)) if x != old])
    expected = "\n".join(new if x == old else x for x in values)
    return make(
        "Replace a word",
        f'Print "words.txt" with every `{old}` replaced by `{new}`. Do not modify the file.',
        1, ["sed"], ds, expected,
        f"sed 's/{old}/{new}/g' words.txt",
        "`sed` is a stream editor. `s/OLD/NEW/g` substitutes every match on each line. Without `-i`, the original file is unchanged."
    )


# users

def users_unique(ds):
    expected = "\n".join(sorted({r["user"] for r in ds.records}))
    return make(
        "Unique users",
        'Print the unique usernames in "users.txt", sorted alphabetically.',
        1, ["sort", "uniq"], ds, expected,
        "sort users.txt | uniq",
        "`sort` puts identical usernames next to each other. `uniq` removes adjacent duplicates."
    )


def users_frequency(ds):
    counts = Counter(r["user"] for r in ds.records)
    ordered = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    expected = "\n".join(f"{count} {name}" for name, count in ordered)
    return make(
        "User frequency table",
        'Print `COUNT USER` for each username, highest count first. Break ties alphabetically.',
        2, ["sort", "uniq", "awk"], ds, expected,
        "sort users.txt | uniq -c | sort -k1,1nr -k2,2 | awk '{print $1, $2}'",
        "`uniq -c` counts adjacent duplicate lines. `sort -k1,1nr -k2,2` sorts the count numerically descending and username alphabetically for ties. The final `awk` normalizes spacing."
    )


# requests.csv

def csv_status_ips(ds):
    target = random.choice([404, 500, 502])
    expected = "\n".join(r["ip"] for r in ds.records if r["status"] == target)
    return make(
        "Extract IPs by HTTP status",
        f'From "requests.csv", print only IP addresses for rows with HTTP status {target}, preserving order.',
        2, ["awk"], ds, expected,
        f"awk -F, 'NR>1 && $5 == {target} {{print $2}}' requests.csv",
        f"`-F,` uses comma as the separator. `NR>1` skips the header. `$5 == {target}` checks the status field and `$2` is the IP."
    )


def csv_count_status(ds):
    target = random.choice([200, 404, 500])
    count = sum(1 for r in ds.records if r["status"] == target)
    return make(
        "Count HTTP responses",
        f'Print only the number of requests with status {target} in "requests.csv".',
        2, ["awk"], ds, str(count),
        f"awk -F, 'NR>1 && $5 == {target} {{c++}} END {{print c+0}}' requests.csv",
        "`c++` increments a counter for each match. `END` runs after all rows. `c+0` guarantees a numeric zero if nothing matched."
    )


def csv_slow_paths(ds):
    threshold = random.choice([300, 500, 800, 1000])
    expected = "\n".join(r["path"] for r in ds.records if r["duration_ms"] > threshold)
    return make(
        "Find slow HTTP requests",
        f'From "requests.csv", print the path for every request slower than {threshold} ms, preserving order.',
        2, ["awk"], ds, expected,
        f"awk -F, 'NR>1 && $7 > {threshold} {{print $4}}' requests.csv",
        "`$7` is `duration_ms` and `$4` is the path. The condition keeps only rows above the threshold."
    )


def csv_top_failing_ip(ds):
    counts = Counter(r["ip"] for r in ds.records if r["status"] >= 500)
    winner = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
    expected = f"{winner[1]} {winner[0]}"
    return make(
        "Incident: top 5xx client",
        'Find the IP with the most HTTP 5xx responses in "requests.csv". Print `COUNT IP`, breaking ties alphabetically.',
        3, ["awk", "sort", "uniq", "head"], ds, expected,
        "awk -F, 'NR>1 && $5 >= 500 {print $2}' requests.csv | sort | uniq -c | sort -k1,1nr -k2,2 | head -1 | awk '{print $1, $2}'",
        "The first `awk` extracts client IPs for 5xx rows. `sort | uniq -c` groups and counts them. The next sort ranks by count descending and IP alphabetically. `head -1` keeps the winner."
    )


def csv_unique_paths(ds):
    expected = "\n".join(sorted({r["path"] for r in ds.records}))
    return make(
        "Unique HTTP paths",
        'Print every unique path from "requests.csv", sorted alphabetically.',
        2, ["tail", "cut", "sort"], ds, expected,
        "tail -n +2 requests.csv | cut -d, -f4 | sort -u",
        "`tail -n +2` skips the header. `cut -d, -f4` extracts CSV field 4. `sort -u` sorts and removes duplicates."
    )


# nginx

def nginx_status_lines(ds):
    target = random.choice([404, 500, 502])
    source_lines = ds.files["access.log"].splitlines()
    expected = "\n".join(line for line, r in zip(source_lines, ds.records) if r["status"] == target)
    return make(
        "Filter nginx status",
        f'Print complete lines from "access.log" whose HTTP status is {target}.',
        1, ["awk"], ds, expected,
        f"awk '$9 == {target}' access.log",
        "In this nginx format the status is field 9. An `awk` condition with no explicit action prints matching lines."
    )


def nginx_unique_ips(ds):
    expected = "\n".join(sorted({r["ip"] for r in ds.records}))
    return make(
        "Unique nginx clients",
        'Print unique client IP addresses in "access.log", sorted alphabetically.',
        1, ["awk", "sort"], ds, expected,
        "awk '{print $1}' access.log | sort -u",
        "The client IP is field 1. `sort -u` sorts and deduplicates."
    )


def nginx_top_ip(ds):
    counts = Counter(r["ip"] for r in ds.records)
    winner = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
    return make(
        "Most active nginx client",
        'Print the most frequent client from "access.log" as `COUNT IP`. Break ties alphabetically.',
        2, ["awk", "sort", "uniq", "head"], ds, f"{winner[1]} {winner[0]}",
        "awk '{print $1}' access.log | sort | uniq -c | sort -k1,1nr -k2,2 | head -1 | awk '{print $1, $2}'",
        "Extract field 1, group identical IPs, count them, rank the counts, and keep the first row."
    )


def nginx_slow_paths(ds):
    threshold = random.choice([400, 700, 1000])
    expected = "\n".join(r["path"] for r in ds.records if r["duration_ms"] > threshold)
    return make(
        "Slow nginx paths",
        f'Print the path for every request in "access.log" slower than {threshold} ms, preserving order.',
        2, ["awk"], ds, expected,
        f"awk '$11+0 > {threshold} {{print $7}}' access.log",
        "The path is field 7. Duration is field 11 and looks like `812ms`; adding `+0` makes `awk` use its numeric prefix."
    )


# auth

def auth_failed_lines(ds):
    expected = "\n".join(r["line"] for r in ds.records if r["outcome"] == "failed")
    return make(
        "SSH failures",
        'Print every failed SSH authentication line from "auth.log".',
        1, ["grep"], ds, expected,
        "grep 'Failed password' auth.log",
        "`grep` prints complete lines containing the supplied text pattern."
    )


def auth_failed_ips(ds):
    expected = "\n".join(r["ip"] for r in ds.records if r["outcome"] == "failed")
    return make(
        "Extract failed SSH source IPs",
        'Print only the source IP for every failed SSH authentication in "auth.log", preserving order.',
        2, ["awk"], ds, expected,
        r'''awk '/Failed password/ {for (i=1; i<=NF; i++) if ($i=="from") print $(i+1)}' auth.log''',
        "Some rows contain `invalid user`, so fixed field numbers are unreliable. This loops through fields, finds the literal `from`, and prints the next field."
    )


def auth_top_failed_ip(ds):
    counts = Counter(r["ip"] for r in ds.records if r["outcome"] == "failed")
    winner = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0]
    return make(
        "Incident: SSH brute-force source",
        'Find the IP with the most failed SSH logins in "auth.log". Print `COUNT IP`, breaking ties alphabetically.',
        3, ["awk", "sort", "uniq", "head"], ds, f"{winner[1]} {winner[0]}",
        r'''awk '/Failed password/ {for (i=1; i<=NF; i++) if ($i=="from") print $(i+1)}' auth.log | sort | uniq -c | sort -k1,1nr -k2,2 | head -1 | awk '{print $1, $2}' ''',
        "First extract the field after `from`, then group, count and rank the IPs."
    )


# app key=value

def app_error_lines(ds):
    source_lines = ds.files["app.log"].splitlines()
    expected = "\n".join(line for line, r in zip(source_lines, ds.records) if r["level"] == "ERROR")
    return make(
        "Application errors",
        'Print complete ERROR lines from "app.log".',
        1, ["grep"], ds, expected,
        "grep 'level=ERROR' app.log",
        "`grep` selects lines containing the exact key/value pair `level=ERROR`."
    )


def app_error_services(ds):
    expected = "\n".join(r["service"] for r in ds.records if r["level"] == "ERROR")
    return make(
        "Services producing errors",
        'Print only the service name for each ERROR entry in "app.log", preserving order.',
        2, ["awk"], ds, expected,
        r'''awk '/level=ERROR/ {for(i=1;i<=NF;i++) if($i~/^service=/){split($i,a,"="); print a[2]}}' app.log''',
        "The regex selects ERROR lines. The loop finds the `service=` field. `split` separates key and value, and `a[2]` is the service name."
    )


def app_slow_services(ds):
    threshold = random.choice([400, 700, 1000])
    expected = "\n".join(r["service"] for r in ds.records if r["duration_ms"] > threshold)
    solution = rf'''awk '{{svc="";d=0;for(i=1;i<=NF;i++){{if($i~/^service=/){{split($i,a,"=");svc=a[2]}};if($i~/^duration_ms=/){{split($i,b,"=");d=b[2]}}}};if(d>{threshold})print svc}}' app.log'''
    return make(
        "Slow application events",
        f'Print the service name for entries in "app.log" with duration_ms greater than {threshold}, preserving order.',
        3, ["awk"], ds, expected, solution,
        "The program scans key=value fields, extracts `service` and `duration_ms`, then prints the service when the duration exceeds the threshold."
    )


# JSONL

def json_errors(ds):
    expected = "\n".join(r["service"] for r in ds.records if r["level"] == "ERROR")
    return make(
        "JSON error services",
        'From "events.jsonl", print the service value for every object whose level is ERROR.',
        2, ["jq"], ds, expected,
        r'''jq -r 'select(.level == "ERROR") | .service' events.jsonl''',
        "`select(...)` keeps matching JSON objects. `.service` extracts that field. `-r` prints raw strings without JSON quotes."
    )


def json_slow(ds):
    threshold = random.choice([500, 800, 1000])
    expected = "\n".join(r["service"] for r in ds.records if r["duration_ms"] > threshold)
    return make(
        "Slow JSON events",
        f'From "events.jsonl", print service names for objects with duration_ms > {threshold}, preserving order.',
        2, ["jq"], ds, expected,
        rf'''jq -r 'select(.duration_ms > {threshold}) | .service' events.jsonl''',
        "`select(.duration_ms > N)` filters numerically. `.service` extracts the requested field."
    )


def json_count_500(ds):
    count = sum(1 for r in ds.records if r["status"] == 500)
    return make(
        "Count JSON status values",
        'Print only the number of objects in "events.jsonl" whose status is 500.',
        2, ["jq", "wc"], ds, str(count),
        r'''jq -r 'select(.status == 500) | .status' events.jsonl | wc -l''',
        "`jq` emits one line for each matching object. `wc -l` counts those lines."
    )


# ps

def ps_top_cpu(ds):
    winner = sorted(ds.records, key=lambda r: (-r["cpu"], r["pid"]))[0]
    return make(
        "Top CPU process",
        'From "processes.txt", print `PID %CPU` for the process using the most CPU.',
        2, ["tail", "sort", "head", "awk"], ds, f'{winner["pid"]} {winner["cpu"]:.1f}',
        "tail -n +2 processes.txt | sort -k3,3nr -k2,2n | head -1 | awk '{print $2, $3}'",
        "Skip the header, sort CPU field 3 numerically descending, use PID as a tie-breaker, keep the first row, then print PID and CPU."
    )


def ps_over_cpu(ds):
    threshold = random.choice([25, 40, 60])
    expected = "\n".join(str(r["pid"]) for r in ds.records if r["cpu"] > threshold)
    return make(
        "Processes above CPU threshold",
        f'Print only PIDs from "processes.txt" whose %CPU is greater than {threshold}, preserving file order.',
        2, ["awk"], ds, expected,
        f"awk 'NR>1 && $3 > {threshold} {{print $2}}' processes.txt",
        "`NR>1` skips the header, `$3` is CPU, and `$2` is PID."
    )


# df

def df_high_usage(ds):
    threshold = random.choice([70, 80, 85])
    expected = "\n".join(r["mount"] for r in ds.records if r["percent"] > threshold)
    return make(
        "High disk usage",
        f'From "df.txt", print mount points whose Use% is greater than {threshold}%, preserving order.',
        2, ["awk"], ds, expected,
        f'''awk 'NR>1 {{p=$5; sub(/%/,"",p); if (p > {threshold}) print $6}}' df.txt''',
        "`$5` contains values such as `87%`. `sub` removes `%` from a copy so the value can be compared numerically. `$6` is the mount point."
    )


def df_most_used(ds):
    winner = sorted(ds.records, key=lambda r: (-r["percent"], r["mount"]))[0]
    return make(
        "Most utilized filesystem",
        'From "df.txt", print `Use% MOUNT` for the most utilized filesystem.',
        2, ["tail", "sort", "head", "awk"], ds, f'{winner["percent"]}% {winner["mount"]}',
        "tail -n +2 df.txt | sort -k5,5nr -k6,6 | head -1 | awk '{print $5, $6}'",
        "Sort Use% numerically in reverse, use mount point as tie-breaker, keep the top row, then print Use% and mount."
    )


# config

def config_active(ds):
    expected = "\n".join(r["line"] for r in ds.records)
    return make(
        "Active configuration",
        'Print only active lines from "service.conf": exclude comments and blank lines.',
        2, ["grep"], ds, expected,
        r'''grep -vE '^[[:space:]]*(#|$)' service.conf''',
        "`-E` enables extended regex syntax and `-v` inverts the match. The regex describes comments or blank lines, so those are excluded."
    )


# filetree

def tree_find_logs(ds):
    expected = "\n".join(sorted(f'./{r["path"]}' for r in ds.records if r["path"].endswith(".log")))
    return make(
        "Find log files",
        'From the exercise directory, print every `.log` file recursively, sorted alphabetically. Paths must begin with `./`.',
        2, ["find", "sort"], ds, expected,
        "find . -type f -name '*.log' | sort",
        "`find .` searches recursively. `-type f` keeps files. `-name '*.log'` filters names. Quotes prevent the shell from expanding the wildcard first."
    )


TASKS_BY_KIND: dict[str, list[Task]] = {
    "words": [words_count_words, words_count_lines, words_replace],
    "users": [users_unique, users_frequency],
    "requests_csv": [csv_status_ips, csv_count_status, csv_slow_paths, csv_top_failing_ip, csv_unique_paths],
    "nginx": [nginx_status_lines, nginx_unique_ips, nginx_top_ip, nginx_slow_paths],
    "auth": [auth_failed_lines, auth_failed_ips, auth_top_failed_ip],
    "app_kv": [app_error_lines, app_error_services, app_slow_services],
    "jsonl": [json_errors, json_slow, json_count_500],
    "ps": [ps_top_cpu, ps_over_cpu],
    "df": [df_high_usage, df_most_used],
    "config": [config_active],
    "filetree": [tree_find_logs],
}
