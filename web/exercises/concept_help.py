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


HELP.update({
    # shell
    "shell.redirection.output": SkillHelp(
        "Output redirection sends stdout into a file. A single > replaces the file's previous contents.",
        "command > file",
        "printf 'ok\\n' > result.txt",
        "Put > after the command whose stdout should become the file contents.",
    ),
    "shell.redirection.append": SkillHelp(
        "Append redirection writes stdout at the end of an existing file instead of replacing it.",
        "command >> file",
        "printf 'next\\n' >> result.txt",
        "Use >> when earlier content must remain in the destination file.",
    ),
    "shell.redirection.stderr": SkillHelp(
        "File descriptor 2 is standard error. 2> redirects errors without redirecting normal stdout.",
        "command 2> errors.txt",
        "cat missing.txt 2> errors.txt",
        "Keep stdout and stderr conceptually separate; redirect descriptor 2 for errors.",
    ),
    "shell.boolean.and": SkillHelp(
        "With &&, the command on the right runs only when the command on the left exits successfully.",
        "command1 && command2",
        "test -f config.ini && cat config.ini",
        "Use && when the second action depends on the first one succeeding.",
    ),
    "shell.boolean.or": SkillHelp(
        "With ||, the command on the right runs only when the command on the left fails.",
        "command1 || command2",
        "test -f config.ini || echo missing",
        "Use || for a fallback action after failure.",
    ),
    "shell.sequence": SkillHelp(
        "A semicolon separates commands and runs the next command regardless of the previous exit status.",
        "command1 ; command2",
        "printf 'first\\n'; printf 'second\\n'",
        "Use ; when ordering matters but success of the first command does not control the second.",
    ),
    "shell.subshell": SkillHelp(
        "Parentheses run a group of commands in a subshell and let the group behave like one pipeline stage.",
        "( command1 ; command2 ) | command3",
        "(printf 'b\\n'; printf 'a\\n') | sort",
        "Group the commands whose combined stdout should feed the next stage.",
    ),

    # grep
    "grep.ignore_case": SkillHelp(
        "grep -i ignores uppercase/lowercase differences while matching.",
        "grep -i 'pattern' file",
        "grep -i 'warning' app.log",
        "Use -i when capitalization should not affect whether a line matches.",
    ),
    "grep.fixed": SkillHelp(
        "grep -F treats the pattern as plain text, so regex characters lose their special meaning.",
        "grep -F 'literal[text]' file",
        "grep -F 'a+b' expressions.txt",
        "Use -F when the search text itself contains regex-looking punctuation.",
    ),
    "grep.word": SkillHelp(
        "grep -w requires the match to occupy a whole word rather than being embedded inside a larger word.",
        "grep -w 'word' file",
        "grep -w 'cat' words.txt",
        "Use -w when substring matches would be false positives.",
    ),
    "grep.count": SkillHelp(
        "grep -c prints the number of matching lines instead of printing each matching line.",
        "grep -c 'pattern' file",
        "grep -c 'ERROR' server.log",
        "If only the count is required, let grep count its own matching lines.",
    ),
    "grep.line_numbers": SkillHelp(
        "grep -n prefixes each matching line with its 1-based line number.",
        "grep -n 'pattern' file",
        "grep -n 'TODO' notes.txt",
        "Use -n when the output must identify where each match occurred.",
    ),
    "grep.multiple_patterns": SkillHelp(
        "Each -e adds another pattern; a line is kept if any supplied pattern matches.",
        "grep -e 'foo' -e 'bar' file",
        "grep -e 'WARN' -e 'ERROR' app.log",
        "Use multiple -e options when the alternatives should stay as separate patterns.",
    ),
    "grep.context": SkillHelp(
        "-A, -B and -C include lines after, before, or around a matching line.",
        "grep -A 2 'pattern' file",
        "grep -B 1 'FAILED' jobs.log",
        "First locate the match, then choose how many surrounding lines belong in the result.",
    ),
    "grep.recursive": SkillHelp(
        "grep -r descends through directories and searches regular files recursively.",
        "grep -r 'pattern' directory",
        "grep -rl 'TODO' .",
        "Use recursive grep when the search target is a directory tree rather than one known file.",
    ),

    # sort
    "sort.delimiter": SkillHelp(
        "sort -t chooses the field delimiter used by -k key definitions.",
        "sort -t, -k3,3 file.csv",
        "sort -t: -k2,2 accounts.txt",
        "Set the delimiter before choosing the key column in delimited data.",
    ),
    "sort.human": SkillHelp(
        "sort -h understands human-readable magnitude suffixes such as K, M and G.",
        "sort -h sizes.txt",
        "printf '900K\\n2G\\n12M\\n' | sort -h",
        "Use -h when numeric values contain size suffixes that plain -n does not interpret correctly.",
    ),
    "sort.version": SkillHelp(
        "sort -V compares version-like strings by their embedded numeric components.",
        "sort -V versions.txt",
        "printf 'v1.10\\nv1.2\\n' | sort -V",
        "Use -V when lexical order would place version 1.10 before 1.2.",
    ),
    "sort.month": SkillHelp(
        "sort -M recognizes month abbreviations and orders them January through December.",
        "sort -M months.txt",
        "printf 'Dec\\nJan\\nFeb\\n' | sort -M",
        "Use -M when the leading sort key is a month name rather than ordinary text.",
    ),
    "sort.stable": SkillHelp(
        "sort -s disables the final whole-line tie breaker, preserving input order when selected keys compare equal.",
        "sort -s -k1,1 file",
        "sort -s -k2,2 records.txt",
        "Use -s when records with equal keys must remain in their original relative order.",
    ),

    # uniq
    "uniq.duplicates_only": SkillHelp(
        "uniq -d prints one representative line for each adjacent group that appears more than once.",
        "uniq -d sorted.txt",
        "sort names.txt | uniq -d",
        "Make equal values adjacent first, then use -d to keep only repeated groups.",
    ),
    "uniq.unique_only": SkillHelp(
        "uniq -u prints only adjacent groups that occur exactly once.",
        "uniq -u sorted.txt",
        "sort names.txt | uniq -u",
        "Use -u when repeated values should disappear completely rather than collapse to one copy.",
    ),
    "uniq.ignore_case": SkillHelp(
        "uniq -i compares adjacent lines case-insensitively.",
        "uniq -i file",
        "uniq -i mixed-case.txt",
        "The lines still need to be adjacent; -i only changes how equality is tested.",
    ),
    "uniq.skip_fields": SkillHelp(
        "uniq -f N ignores the first N whitespace-separated fields during comparison.",
        "uniq -f 1 file",
        "uniq -f 2 records.txt",
        "Skip volatile leading fields when duplicates should be determined by the remainder of each line.",
    ),

    # wc
    "wc.bytes": SkillHelp(
        "wc -c counts bytes in its input.",
        "wc -c < file",
        "printf 'abc' | wc -c",
        "Use byte counting when storage size, not words or lines, is the requested unit.",
    ),
    "wc.chars": SkillHelp(
        "wc -m counts characters according to the current locale, which can differ from byte count for Unicode text.",
        "wc -m < file",
        "printf 'café\\n' | wc -m",
        "Use -m when the problem explicitly asks for characters rather than bytes.",
    ),
    "wc.multiple": SkillHelp(
        "wc can request several metrics at once by combining options.",
        "wc -lw < file",
        "wc -lc < log.txt",
        "Choose every requested metric, but remember wc prints them in its standard column order.",
    ),

    # sed
    "sed.address": SkillHelp(
        "A sed address limits the following command to a specific line number or matching pattern.",
        "sed '3s/old/new/' file",
        "sed '/ERROR/s/dev/prod/' file",
        "Put the address immediately before the sed command that should only apply there.",
    ),
    "sed.range": SkillHelp(
        "Two addresses separated by a comma define a range where the following sed command applies.",
        "sed '2,5s/old/new/g' file",
        "sed '/BEGIN/,/END/d' file",
        "Identify where the range starts and ends before choosing the operation.",
    ),
    "sed.delete": SkillHelp(
        "The d command deletes selected pattern-space lines from sed output.",
        "sed '/pattern/d' file",
        "sed '/^#/d' config.conf",
        "Write an address that identifies unwanted lines, then apply d.",
    ),
    "sed.print_only": SkillHelp(
        "sed -n suppresses automatic printing; p then prints only explicitly selected lines.",
        "sed -n '/pattern/p' file",
        "sed -n '/=/p' config.conf",
        "Pair -n with p so only the addressed lines are emitted.",
    ),
    "sed.backrefs": SkillHelp(
        "Capture groups remember matched text; \\1, \\2 and later backreferences reuse those groups in a replacement.",
        "sed -E 's/^([^:]+):(.+)$/\\2 \\1/' file",
        "sed -E 's/^([0-9]+) (.*)$/\\2 [\\1]/' records.txt",
        "Capture the parts you need to rearrange, then reference those captures in the replacement.",
    ),
    "sed.multiple_expr": SkillHelp(
        "Multiple -e options apply several sed programs in order to the same input stream.",
        "sed -e 's/foo/bar/' -e 's/baz/qux/' file",
        "sed -e 's/WARN/W/' -e 's/ERROR/E/' log",
        "Use one -e for each independent transformation you want sed to perform.",
    ),
    "sed.iac": SkillHelp(
        "sed i, a and c insert before, append after, or replace a selected line.",
        "sed '2c\\replacement text' file",
        "sed '/marker/a\\added line' file",
        "Choose the address first, then decide whether the new line belongs before, after, or instead of it.",
    ),

    # find
    "find.size": SkillHelp(
        "find -size filters files by size. A leading + means larger than, and c uses byte units.",
        "find . -type f -size +100c",
        "find logs -type f -size -1M",
        "Choose the comparison sign and unit carefully; +N means greater than N units.",
    ),
    "find.depth": SkillHelp(
        "-maxdepth and -mindepth constrain how far find descends from the starting path.",
        "find . -maxdepth 2 -type f",
        "find . -mindepth 2 -type d",
        "Count the starting path as depth 0 when deciding the desired boundary.",
    ),
    "find.logic": SkillHelp(
        "find predicates can be combined with implicit AND, explicit -o for OR, and !/-not for negation.",
        "find . -type f \\( -name '*.log' -o -name '*.json' \\)",
        "find . -type f ! -name '*.tmp'",
        "Use escaped parentheses when OR alternatives should be grouped together.",
    ),
    "find.exec": SkillHelp(
        "find -exec runs another command with each selected path substituted at {}.",
        "find . -type f -exec basename {} \\;",
        "find . -name '*.log' -exec wc -l {} \\;",
        "Place {} where the selected pathname should be passed, then terminate -exec with an escaped semicolon.",
    ),
    "find.path": SkillHelp(
        "find -path matches the whole path produced by find, not just the final filename.",
        "find . -path './logs/*'",
        "find . -type f -path '*/archive/*'",
        "Use -path when directory components are part of the selection rule.",
    ),

    # jq
    "jq.boolean": SkillHelp(
        "jq combines boolean expressions with the words and, or and not rather than shell-style && and ||.",
        "select((.a == 1) and (.b != 2))",
        "jq 'select((.level == \"ERROR\") or (.status >= 500))' events.jsonl",
        "Put complete comparisons on each side of and/or inside select().",
    ),
    "jq.multi_field": SkillHelp(
        "jq can combine several extracted fields into one output record, often through an array and a formatter such as @tsv.",
        "[.field1, .field2] | @tsv",
        "jq -r '[.user, .status] | @tsv' events.jsonl",
        "Collect the required fields in the requested order before formatting them.",
    ),
    "jq.arrays": SkillHelp(
        "JSON arrays use [] indexing; jq can also construct arrays with [expression].",
        ".items[0]",
        "jq -r '.hosts[1]' config.json",
        "Check whether you are traversing an object key or selecting an array element by index.",
    ),
    "jq.length": SkillHelp(
        "length reports the size of an array/object/string. With -s, JSONL inputs can first be collected into one array.",
        "jq -s 'length' file.jsonl",
        "jq '.items | length' object.json",
        "Make sure length is being applied to the collection you intend to count.",
    ),
    "jq.map": SkillHelp(
        "map(expr) applies an expression to every element of an input array and returns a new array.",
        "map(.field)",
        "jq -s 'map(.status)' events.jsonl",
        "First make sure the input is an array, then describe the transformation for one element.",
    ),
    "jq.sort_by": SkillHelp(
        "sort_by(expr) orders an array according to a field or computed expression.",
        "sort_by(.duration_ms)",
        "jq -s 'sort_by(.score)' results.jsonl",
        "Slurp JSONL into an array when needed, then sort by the requested key.",
    ),
    "jq.group_by": SkillHelp(
        "group_by(expr) collects array elements with equal keys into sub-arrays.",
        "group_by(.service)",
        "jq -s 'group_by(.level)' events.jsonl",
        "After grouping, each result is an array; inspect .[0] for its key and length for its count.",
    ),
    "jq.unique_by": SkillHelp(
        "unique_by(expr) keeps one array element for each distinct value of the expression.",
        "unique_by(.service)",
        "jq -s 'unique_by(.user)' events.jsonl",
        "Choose the field that defines uniqueness rather than deduplicating complete objects accidentally.",
    ),
    "jq.minmax": SkillHelp(
        "min_by(expr) and max_by(expr) return the array element with the smallest or largest key.",
        "max_by(.duration_ms)",
        "jq -s 'max_by(.score)' results.jsonl",
        "Select the winning object first, then extract whichever field the output contract asks for.",
    ),
    "jq.nested": SkillHelp(
        "Nested object fields are traversed by chaining selectors such as .meta.service.",
        ".outer.inner",
        "jq -r '.request.user' events.jsonl",
        "Follow the object structure one level at a time from the root value.",
    ),
    "jq.construct": SkillHelp(
        "jq object syntax builds a new JSON object whose values can come from the input.",
        "{name: .user, code: .status}",
        "jq -c '{service: .service, ms: .duration_ms}' events.jsonl",
        "Name each desired output key and assign the input expression that should populate it.",
    ),

    # head/tail/cut
    "head.bytes": SkillHelp(
        "head -c emits the first N bytes rather than the first N lines.",
        "head -c 20 file",
        "head -c 8 payload.txt",
        "Use byte mode only when the requested boundary is measured in bytes rather than lines.",
    ),
    "tail.from_line": SkillHelp(
        "tail -n +N starts output at line N and continues through the end of the input.",
        "tail -n +2 file",
        "tail -n +5 table.txt",
        "The plus sign changes the meaning from 'last N lines' to 'start at line N'.",
    ),
    "tail.bytes": SkillHelp(
        "tail -c emits bytes from the end of the input.",
        "tail -c 20 file",
        "tail -c 8 payload.txt",
        "Use -c when the suffix length is measured in bytes rather than lines.",
    ),
    "cut.multiple_fields": SkillHelp(
        "cut accepts comma-separated field numbers to emit several non-adjacent columns.",
        "cut -d, -f1,3 file.csv",
        "cut -d: -f1,6 accounts.txt",
        "List the desired field numbers in output order after -f.",
    ),
    "cut.range": SkillHelp(
        "cut field ranges such as 2-4 select every field from the start through the end of that range.",
        "cut -d, -f2-4 file.csv",
        "cut -d: -f1-3 accounts.txt",
        "Use a range when the requested columns are contiguous.",
    ),
    "cut.complement": SkillHelp(
        "--complement inverts the field selection and emits every field except those named by -f.",
        "cut -d, --complement -f1 file.csv",
        "cut -d: --complement -f2 accounts.txt",
        "Identify the column to exclude rather than enumerating every column to keep.",
    ),
    "cut.characters": SkillHelp(
        "cut -c selects character positions from each input line without using a delimiter.",
        "cut -c1-5 file",
        "cut -c1,3,5 codes.txt",
        "Use character mode for fixed-position text rather than delimited columns.",
    ),
})


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
