from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillHelp:
    concept: str
    syntax: str
    example: str
    hint: str


HELP: dict[str, SkillHelp] = {
    "shell.pipeline.basic": SkillHelp(
        "A pipe sends stdout from the command on the left into stdin of the command on the right.",
        "command1 | command2",
        "printf 'b\\na\\n' | sort",
        "Think of the first command as producing data and the second as transforming that data.",
    ),
    "shell.pipeline.multi": SkillHelp(
        "A multi-stage pipeline transforms data one step at a time through several commands.",
        "command1 | command2 | command3",
        "printf 'b\\na\\na\\n' | sort | uniq",
        "Build the pipeline incrementally and inspect the output after each stage.",
    ),
    "shell.redirection.input": SkillHelp(
        "Input redirection feeds a file to a command through stdin. This often prevents the command from printing the filename.",
        "command < file",
        "wc -l < example.txt",
        "Ask whether the command should read the file as an argument or receive its contents on stdin.",
    ),
    "awk.fields": SkillHelp(
        "AWK splits each input row into fields. $0 is the whole row; $1, $2 and so on are individual fields.",
        "awk '{print $1, $2}' file",
        "awk '{print $1}' users.txt",
        "Identify which field contains the value you need, then print that field.",
    ),
    "awk.separator": SkillHelp(
        "AWK normally splits on whitespace. -F changes the input field separator, which is useful for CSV or other delimited data.",
        "awk -F, '{print $2}' file.csv",
        "awk -F: '{print $1}' accounts.txt",
        "Look at the file delimiter first, then tell AWK how to split each row.",
    ),
    "awk.conditions": SkillHelp(
        "An AWK pattern can be a condition. The action runs only for rows where that condition is true.",
        "awk '$3 > 50 {print $1}' file",
        "awk '$2 == \"ERROR\" {print $1}' events.txt",
        "First identify the field to test, then write the comparison before the action block.",
    ),
    "awk.nr_nf": SkillHelp(
        "NR is the current input row number. NF is the number of fields in the current row.",
        "awk 'NR > 1 {print $1}' file",
        "awk '{print NF}' records.txt",
        "Use NR when the position of the row matters; use NF when the number or last position of fields matters.",
    ),
    "awk.regex": SkillHelp(
        "A /regex/ pattern selects rows whose full text matches. The ~ and !~ operators test a specific field against a regex.",
        "awk '/ERROR/ {print $0}' file",
        "awk '$2 ~ /^err/ {print $1}' events.txt",
        "Use /pattern/ for whole-line matching, or field ~ /pattern/ when only one field should be tested.",
    ),
    "awk.variables_end": SkillHelp(
        "AWK variables can accumulate state while rows are processed. END runs once after all input has been read.",
        "awk 'condition {count++} END {print count}' file",
        "awk '/ERROR/ {n++} END {print n+0}' server.log",
        "Think in three steps: match a row, update a counter, then print the accumulated value in END.",
    ),
    "awk.loops": SkillHelp(
        "AWK for loops can walk through all fields or through values stored in an array.",
        "for (i=1; i<=NF; i++) { ... }",
        "awk '{for (i=1; i<=NF; i++) print $i}' records.txt",
        "Use a loop when the interesting field cannot be identified by one fixed position.",
    ),
    "awk.dynamic_fields": SkillHelp(
        "When a variable contains a field number, $i means the field whose number is stored in i. $(i+1) refers to a field relative to it.",
        "if ($i == \"marker\") print $(i+1)",
        "awk '{for(i=1;i<=NF;i++) if($i==\"user\") print $(i+1)}' file",
        "Search for a stable marker, then extract the field next to that marker instead of hard-coding a column number.",
    ),
    "awk.split": SkillHelp(
        "split() breaks one string into pieces and stores them in an AWK array.",
        "split(value, parts, \"=\")",
        "awk '{split($2,a,\"=\"); print a[2]}' file",
        "If one field itself contains a delimiter, split that field before extracting the part you need.",
    ),
    "awk.substitution": SkillHelp(
        "sub() replaces the first match; gsub() replaces every match. They can clean a field before comparison or output.",
        "sub(/pattern/, \"replacement\", variable)",
        "awk '{x=$1; sub(/%/,\"\",x); print x}' file",
        "Copy the field into a variable if you want to clean it without changing the original row.",
    ),
    "awk.assoc_arrays": SkillHelp(
        "AWK associative arrays use strings or numbers as keys. They are useful for counting values such as users, statuses or IPs.",
        "count[$1]++",
        "awk '{count[$1]++} END {for (k in count) print k, count[k]}' file",
        "Use the value you want to group by as the array key, and increment that array element for every row.",
    ),
    "awk.aggregation": SkillHelp(
        "AWK can group and summarize data internally with associative arrays, then emit the results in END.",
        "{count[key]++} END {for (k in count) print k, count[k]}",
        "awk '{c[$2]++} END {for(k in c) print k,c[k]}' file",
        "Separate the problem into grouping during input and reporting after input.",
    ),
    "grep.literal": SkillHelp(
        "grep prints input lines containing a matching text pattern.",
        "grep 'text' file",
        "grep 'ERROR' server.log",
        "Choose a distinctive piece of text that appears on every line you want to keep.",
    ),
    "grep.invert": SkillHelp(
        "grep -v reverses the selection and keeps lines that do not match the pattern.",
        "grep -v 'text' file",
        "grep -v '^#' config.conf",
        "Describe the lines you want to exclude, then invert that match.",
    ),
    "grep.regex": SkillHelp(
        "Regular expressions let grep match structure rather than one literal string, using anchors and character classes.",
        "grep '^pattern' file",
        "grep '^[0-9]' data.txt",
        "Use ^ for the start of a line and $ for the end when position matters.",
    ),
    "grep.extended": SkillHelp(
        "grep -E enables extended regex syntax such as alternation with | and grouping with parentheses.",
        "grep -E 'foo|bar' file",
        "grep -E '^(WARN|ERROR)' app.log",
        "When one pattern should match several alternatives, combine them with -E and |.",
    ),
    "sort.basic": SkillHelp(
        "sort orders complete input lines using normal text order unless another comparison mode is requested.",
        "sort file",
        "printf 'beta\\nalpha\\n' | sort",
        "Decide whether ordinary text order is actually the ordering the exercise asks for.",
    ),
    "sort.unique": SkillHelp(
        "sort -u sorts lines and removes duplicates in the same operation.",
        "sort -u file",
        "sort -u users.txt",
        "If you need both sorting and deduplication, one sort option can do both.",
    ),
    "sort.numeric_reverse": SkillHelp(
        "sort -n compares numbers numerically and -r reverses the ordering.",
        "sort -nr file",
        "printf '2\\n10\\n5\\n' | sort -nr",
        "Text sorting and numeric sorting differ for values such as 2 and 10.",
    ),
    "sort.keys": SkillHelp(
        "-k selects which field or field range should be used as the sort key.",
        "sort -k2,2 file",
        "sort -k3,3n processes.txt",
        "Identify the field that should determine order, then make that field the key.",
    ),
    "sort.multiple_keys": SkillHelp(
        "Multiple -k options define a primary sort key and one or more tie-breakers.",
        "sort -k1,1nr -k2,2 file",
        "sort -k2,2n -k1,1 users.txt",
        "Write the main ordering first, then add another key that decides equal cases.",
    ),
    "uniq.basic": SkillHelp(
        "uniq removes repeated adjacent lines. Equal values must already be next to each other.",
        "uniq file",
        "sort users.txt | uniq",
        "Ask whether duplicates are adjacent yet; if not, something must group them first.",
    ),
    "uniq.count": SkillHelp(
        "uniq -c prefixes each adjacent duplicate group with the number of lines in that group.",
        "uniq -c file",
        "sort users.txt | uniq -c",
        "Group identical lines first, then count the groups.",
    ),
    "wc.lines": SkillHelp(
        "wc -l counts newline-delimited input lines.",
        "wc -l file",
        "grep 'ERROR' log | wc -l",
        "If each matching record is one output line, line counting can turn that stream into a total.",
    ),
    "wc.words": SkillHelp(
        "wc -w counts whitespace-separated words from a file or stdin.",
        "wc -w file",
        "wc -w < notes.txt",
        "Use word counting when the unit being counted is tokens rather than rows.",
    ),
    "sed.substitute": SkillHelp(
        "sed substitution replaces text while streaming input; without -i it prints transformed output without modifying the file.",
        "sed 's/old/new/' file",
        "sed 's/dev/prod/' config.txt",
        "Put the text to replace and its replacement inside an s/// expression.",
    ),
    "sed.global": SkillHelp(
        "The g flag on a sed substitution replaces every match on each line instead of only the first.",
        "sed 's/old/new/g' file",
        "sed 's/:/-/g' values.txt",
        "If the pattern can occur more than once on a row, decide whether the g flag is required.",
    ),
    "find.name_type": SkillHelp(
        "find walks a directory tree. -type limits object type and -name matches filenames.",
        "find . -type f -name '*.log'",
        "find . -type f -name '*.conf'",
        "Start from the required directory, then narrow the search by type and name.",
    ),
    "jq.field": SkillHelp(
        "jq uses .field syntax to extract a property from each JSON object.",
        "jq '.field' file.jsonl",
        "jq '.service' events.jsonl",
        "Inspect the JSON keys, then address the one you need with a leading dot.",
    ),
    "jq.raw": SkillHelp(
        "jq -r prints string values as raw text instead of JSON strings with quotes.",
        "jq -r '.field' file.jsonl",
        "jq -r '.user' events.jsonl",
        "If the expected output has plain strings rather than quoted JSON strings, raw output is useful.",
    ),
    "jq.select": SkillHelp(
        "select(condition) keeps only JSON values for which the condition is true.",
        "jq 'select(.field == value)' file.jsonl",
        "jq -r 'select(.level == \"WARN\") | .service' events.jsonl",
        "Filter the objects first with select(), then extract the field required by the output format.",
    ),
    "head.basic": SkillHelp(
        "head emits the first part of its input, commonly the first N lines.",
        "head -n 3 file",
        "sort scores.txt | head -1",
        "Put the desired result at the top first, then use head to keep only that portion.",
    ),
    "tail.basic": SkillHelp(
        "tail emits lines from the end, or with -n +N can start output at a chosen line number.",
        "tail -n +2 file",
        "tail -n 5 app.log",
        "For a header, starting at line 2 is often more useful than selecting the final lines.",
    ),
    "cut.fields": SkillHelp(
        "cut extracts delimited fields. -d chooses the delimiter and -f chooses the field number.",
        "cut -d, -f2 file.csv",
        "cut -d: -f1 accounts.txt",
        "Identify the delimiter and the desired column number before building the command.",
    ),
}


def get_help(skill_id: str, fallback_name: str = "this concept", fallback_tool: str = "command") -> SkillHelp:
    return HELP.get(
        skill_id,
        SkillHelp(
            f"Review {fallback_name} before applying it to the exercise.",
            f"man {fallback_tool}",
            f"{fallback_tool} --help",
            f"Focus on {fallback_name} and the requested output format.",
        ),
    )
