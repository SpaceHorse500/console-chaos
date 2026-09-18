from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Callable

from .models import Dataset, Exercise, FieldSpec, OutputSpec, SkillUse


@dataclass
class FilterChoice:
    field: FieldSpec
    op: str
    value: object
    matches: list[dict]
    prompt: str


def skill(skill_id: str, role: str = "target") -> SkillUse:
    return SkillUse(skill_id=skill_id, role=role)


def out(label: str, example: str, *rules: str) -> OutputSpec:
    return OutputSpec(label=label, example=example, rules=list(rules))


def make(ds: Dataset, template_id: str, title: str, prompt: str, style: str,
         tools: list[str], skills: list[SkillUse], output_spec: OutputSpec,
         expected: str, solution: str, explanation: str) -> Exercise:
    return Exercise(
        template_id=template_id,
        title=title,
        prompt=prompt,
        style=style,
        tools=tools,
        skills=skills,
        output=output_spec,
        dataset_kind=ds.kind,
        files=ds.files,
        expected=expected,
        solution=solution,
        explanation=explanation,
    )


def _value(ds: Dataset, field: FieldSpec, record: dict) -> object:
    return record[field.name]


def _display(field: FieldSpec, value: object) -> str:
    if field.decimals is not None and isinstance(value, (int, float)):
        text = f"{float(value):.{field.decimals}f}"
    elif isinstance(value, float):
        text = f"{value:g}"
    else:
        text = str(value)
    return text + field.output_suffix


def _num(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    while text and not (text[-1].isdigit() or text[-1] in ".-"):
        text = text[:-1]
    return float(text)


def _awk_string(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _jq_string(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _awk_prefix(ds: Dataset) -> str:
    if ds.format == "csv":
        return f"awk -F{ds.delimiter}"
    if ds.format == "colon":
        return f"awk -F{ds.delimiter}"
    return "awk"


def _header_clause(ds: Dataset) -> str:
    return f"NR>{ds.header_rows} && " if ds.header_rows else ""


def _awk_field_expr(field: FieldSpec, numeric: bool = False) -> str:
    expr = f"${field.index}"
    if numeric and field.output_suffix:
        return f"({expr}+0)"
    return expr


def _awk_condition(ds: Dataset, choice: FilterChoice) -> str:
    field = choice.field
    prefix = _header_clause(ds)
    if field.type == "number":
        return f"{prefix}{_awk_field_expr(field, True)} {choice.op} {choice.value}"
    return f'{prefix}{_awk_field_expr(field)} {choice.op} "{_awk_string(choice.value)}"'


def _jq_condition(choice: FilterChoice) -> str:
    field = choice.field
    if field.type == "number":
        return f".{field.name} {choice.op} {choice.value}"
    return f'.{field.name} {choice.op} "{_jq_string(choice.value)}"'


def _match(field: FieldSpec, op: str, left: object, right: object) -> bool:
    if field.type == "number":
        a, b = _num(left), _num(right)
    else:
        a, b = str(left), str(right)
    return {
        "==": a == b,
        "!=": a != b,
        ">": a > b,
        "<": a < b,
        ">=": a >= b,
        "<=": a <= b,
    }[op]


def _choose_filter(ds: Dataset, exclude: set[str] | None = None) -> FilterChoice | None:
    exclude = exclude or set()
    fields = [f for f in ds.fields.values() if f.can_filter and f.name not in exclude]
    random.shuffle(fields)
    total = len(ds.records)
    if total < 3:
        return None

    for field in fields:
        values = [_value(ds, field, r) for r in ds.records]
        attempts = []
        if field.type == "number":
            unique = sorted(set(values), key=_num)
            if len(unique) < 3:
                continue
            interior = unique[1:-1]
            random.shuffle(interior)
            ops = list(field.operators)
            random.shuffle(ops)
            for value in interior[:8]:
                for op in ops:
                    attempts.append((op, value))
        else:
            unique = list(dict.fromkeys(values))
            random.shuffle(unique)
            ops = [op for op in field.operators if op in ("==", "!=")]
            for value in unique[:10]:
                for op in ops:
                    attempts.append((op, value))

        random.shuffle(attempts)
        for op, value in attempts:
            matches = [r for r in ds.records if _match(field, op, _value(ds, field, r), value)]
            count = len(matches)
            # Reject empty, all-row and nearly-all-row exercises. With tiny tables,
            # a single matching row is still useful practice.
            if count == 0 or count == total:
                continue
            if total >= 8 and count / total > 0.88:
                continue
            shown = _display(field, value)
            phrase = f'{field.label} {op} {shown}'
            return FilterChoice(field, op, value, matches, phrase)
    return None


def _choose_output_fields(ds: Dataset, avoid: set[str] | None = None, allow_two: bool = True) -> list[FieldSpec]:
    avoid = avoid or set()
    choices = [f for f in ds.fields.values() if f.can_output and f.name not in avoid]
    if not choices:
        choices = [f for f in ds.fields.values() if f.can_output]
    if not choices:
        return []
    random.shuffle(choices)
    count = 2 if allow_two and len(choices) >= 2 and random.random() < 0.28 else 1
    return choices[:count]


def _expected_rows(records: list[dict], fields: list[FieldSpec]) -> str:
    return "\n".join(" ".join(_display(field, record[field.name]) for field in fields) for record in records)


def _output_example(fields: list[FieldSpec]) -> str:
    return " ".join(field.example for field in fields)


def _field_label(fields: list[FieldSpec]) -> str:
    return " ".join(field.label for field in fields)


def _tabular_filter_project(ds: Dataset) -> Exercise | None:
    choice = _choose_filter(ds)
    if not choice:
        return None
    outputs = _choose_output_fields(ds, {choice.field.name})
    if not outputs:
        return None
    condition = _awk_condition(ds, choice)
    print_expr = ", ".join(f"${field.index}" for field in outputs)
    expected = _expected_rows(choice.matches, outputs)
    prompt = f'From "{ds.primary_file}", print {_field_label(outputs)} for rows where {choice.prompt}. Preserve input order.'
    solution = f"{_awk_prefix(ds)} '{condition} {{print {print_expr}}}' {ds.primary_file}"
    skills = [skill("awk.conditions")]
    if ds.format in ("csv", "colon"):
        skills.append(skill("awk.separator", "prerequisite"))
    skills.append(skill("awk.fields", "prerequisite"))
    return make(
        ds,
        f"dynamic.{ds.kind}.filter_project.{choice.field.name}.{'_'.join(f.name for f in outputs)}",
        "Filter and extract fields",
        prompt,
        "focused",
        ["awk"],
        skills,
        out(_field_label(outputs), _output_example(outputs), "One result per matching row.", "Preserve input order.", "Do not print the header." if ds.header_rows else "Do not add a header."),
        expected,
        solution,
        "Use an AWK condition to select rows, then print the requested field or fields. The filter field and output field are intentionally randomized.",
    )


def _json_filter_project(ds: Dataset) -> Exercise | None:
    choice = _choose_filter(ds)
    if not choice:
        return None
    outputs = _choose_output_fields(ds, {choice.field.name}, allow_two=False)
    if not outputs:
        return None
    output_field = outputs[0]
    expected = "\n".join(_display(output_field, r[output_field.name]) for r in choice.matches)
    condition = _jq_condition(choice)
    solution = f"jq -r 'select({condition}) | .{output_field.name}' {ds.primary_file}"
    return make(
        ds,
        f"dynamic.{ds.kind}.filter_project.{choice.field.name}.{output_field.name}",
        "Filter JSON events",
        f'From "{ds.primary_file}", print {output_field.label} for objects where {choice.prompt}. Preserve input order.',
        "focused",
        ["jq"],
        [skill("jq.select"), skill("jq.field", "prerequisite"), skill("jq.raw", "prerequisite")],
        out(output_field.label, output_field.example, "One value per matching object.", "Preserve input order.", "Print raw values without JSON quotes."),
        expected,
        solution,
        "`select(...)` filters JSON objects, then `.field` extracts the requested property. `-r` prints strings as plain text.",
    )


def _tabular_count_filter(ds: Dataset) -> Exercise | None:
    choice = _choose_filter(ds)
    if not choice:
        return None
    condition = _awk_condition(ds, choice)
    expected = str(len(choice.matches))
    solution = f"{_awk_prefix(ds)} '{condition} {{c++}} END {{print c+0}}' {ds.primary_file}"
    skills = [skill("awk.variables_end"), skill("awk.conditions", "prerequisite")]
    if ds.format in ("csv", "colon"):
        skills.append(skill("awk.separator", "prerequisite"))
    return make(
        ds,
        f"dynamic.{ds.kind}.count_filter.{choice.field.name}",
        "Count matching records",
        f'From "{ds.primary_file}", print only the number of data rows where {choice.prompt}.',
        "focused",
        ["awk"],
        skills,
        out("ONE NUMBER", "7", "Print exactly one number."),
        expected,
        solution,
        "Increment an AWK counter for each matching row, then print the final counter in `END`.",
    )


def _json_count_filter(ds: Dataset) -> Exercise | None:
    choice = _choose_filter(ds)
    if not choice:
        return None
    condition = _jq_condition(choice)
    expected = str(len(choice.matches))
    solution = f"jq -r 'select({condition}) | 1' {ds.primary_file} | wc -l"
    return make(
        ds,
        f"dynamic.{ds.kind}.count_filter.{choice.field.name}",
        "Count matching JSON objects",
        f'From "{ds.primary_file}", print only the number of objects where {choice.prompt}.',
        "integration",
        ["jq", "wc"],
        [skill("jq.select"), skill("wc.lines"), skill("shell.pipeline.basic", "reinforcement")],
        out("ONE NUMBER", "7", "Print exactly one number."),
        expected,
        solution,
        "Emit one line for each matching JSON object, then count those lines with `wc -l`.",
    )


def _tabular_unique(ds: Dataset) -> Exercise | None:
    fields = [f for f in ds.fields.values() if f.can_group and f.can_output]
    if not fields:
        return None
    field = random.choice(fields)
    values = sorted({_display(field, r[field.name]) for r in ds.records})
    if len(values) < 2:
        return None
    header = f"NR>{ds.header_rows} " if ds.header_rows else ""
    solution = f"{_awk_prefix(ds)} '{header}{{print ${field.index}}}' {ds.primary_file} | sort -u"
    return make(
        ds,
        f"dynamic.{ds.kind}.unique.{field.name}",
        "Unique field values",
        f'From "{ds.primary_file}", print unique {field.label} values sorted using normal text order.',
        "integration",
        ["awk", "sort"],
        [skill("awk.fields", "reinforcement"), skill("sort.unique"), skill("shell.pipeline.basic", "reinforcement")],
        out(f"ONE {field.label} PER LINE", field.example, "Remove duplicates.", "Sort using normal text order."),
        "\n".join(values),
        solution,
        "Extract the requested field, then use `sort -u` to sort and deduplicate it.",
    )


def _json_unique(ds: Dataset) -> Exercise | None:
    fields = [f for f in ds.fields.values() if f.can_group and f.can_output]
    if not fields:
        return None
    field = random.choice(fields)
    values = sorted({_display(field, r[field.name]) for r in ds.records})
    if len(values) < 2:
        return None
    solution = f"jq -r '.{field.name}' {ds.primary_file} | sort -u"
    return make(
        ds,
        f"dynamic.{ds.kind}.unique.{field.name}",
        "Unique JSON values",
        f'From "{ds.primary_file}", print unique {field.label} values sorted using normal text order.',
        "integration",
        ["jq", "sort"],
        [skill("jq.field", "reinforcement"), skill("jq.raw", "reinforcement"), skill("sort.unique"), skill("shell.pipeline.basic", "reinforcement")],
        out(f"ONE {field.label} PER LINE", field.example, "Remove duplicates.", "Sort using normal text order."),
        "\n".join(values),
        solution,
        "Extract the JSON field as raw text, then sort and deduplicate it.",
    )


def _group_count_common(ds: Dataset, json_mode: bool) -> Exercise | None:
    fields = [f for f in ds.fields.values() if f.can_group and f.can_output]
    random.shuffle(fields)
    for field in fields:
        counts = Counter(_display(field, r[field.name]) for r in ds.records)
        if len(counts) < 2:
            continue
        ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        expected = "\n".join(f"{count} {value}" for value, count in ordered)
        if json_mode:
            extract = f"jq -r '.{field.name}' {ds.primary_file}"
            skills = [skill("jq.field", "reinforcement"), skill("jq.raw", "reinforcement")]
            tools = ["jq", "sort", "uniq", "awk"]
        else:
            header = f"NR>{ds.header_rows} " if ds.header_rows else ""
            extract = f"{_awk_prefix(ds)} '{header}{{print ${field.index}}}' {ds.primary_file}"
            skills = [skill("awk.fields", "reinforcement")]
            if ds.format in ("csv", "colon"):
                skills.append(skill("awk.separator", "reinforcement"))
            tools = ["awk", "sort", "uniq"]
        solution = extract + " | sort | uniq -c | sort -k1,1nr -k2,2 | awk '{print $1, $2}'"
        skills += [skill("uniq.count"), skill("sort.multiple_keys"), skill("shell.pipeline.multi", "reinforcement")]
        return make(
            ds,
            f"dynamic.{ds.kind}.group_count.{field.name}",
            "Frequency table",
            f'From "{ds.primary_file}", print `COUNT {field.label}` for every distinct {field.label}, highest count first. Break ties using normal text order.',
            "integration",
            tools,
            skills,
            out(f"COUNT {field.label}", f"9 {field.example}\n4 another-value", "One distinct value per line.", "Highest count first.", "Break equal counts by value."),
            expected,
            solution,
            "Extract one field, group equal values, count them, then sort by count descending with the value as a tie-breaker.",
        )
    return None


def _range_project(ds: Dataset, json_mode: bool) -> Exercise | None:
    numeric = [f for f in ds.fields.values() if f.can_filter and f.type == "number"]
    random.shuffle(numeric)
    for field in numeric:
        vals = sorted(set(_num(r[field.name]) for r in ds.records))
        if len(vals) < 4:
            continue
        for _ in range(12):
            a, b = sorted(random.sample(vals, 2))
            matches = [r for r in ds.records if a <= _num(r[field.name]) <= b]
            if not matches or len(matches) == len(ds.records):
                continue
            outputs = _choose_output_fields(ds, {field.name}, allow_two=not json_mode)
            if not outputs:
                continue
            if json_mode:
                output_field = outputs[0]
                expected = "\n".join(_display(output_field, r[output_field.name]) for r in matches)
                solution = f"jq -r 'select(.{field.name} >= {a:g} and .{field.name} <= {b:g}) | .{output_field.name}' {ds.primary_file}"
                tools = ["jq"]
                skills = [skill("jq.select"), skill("jq.field", "prerequisite"), skill("jq.raw", "prerequisite")]
                label = output_field.label
                example = output_field.example
            else:
                expected = _expected_rows(matches, outputs)
                cond = f"{_header_clause(ds)}{_awk_field_expr(field, True)} >= {a:g} && {_awk_field_expr(field, True)} <= {b:g}"
                print_expr = ", ".join(f"${x.index}" for x in outputs)
                solution = f"{_awk_prefix(ds)} '{cond} {{print {print_expr}}}' {ds.primary_file}"
                tools = ["awk"]
                skills = [skill("awk.conditions"), skill("awk.fields", "prerequisite")]
                if ds.format in ("csv", "colon"):
                    skills.append(skill("awk.separator", "prerequisite"))
                label = _field_label(outputs)
                example = _output_example(outputs)
            return make(
                ds,
                f"dynamic.{ds.kind}.range.{field.name}.{label.replace(' ', '_')}",
                "Filter a numeric range",
                f'From "{ds.primary_file}", print {label} for rows where {field.label} is between {a:g} and {b:g}, inclusive.',
                "focused",
                tools,
                skills,
                out(label, example, "Preserve input order.", "The range is inclusive."),
                expected,
                solution,
                "Use two numeric comparisons joined by AND so only records inside the requested range are printed.",
            )
    return None


def _tabular_sum_or_average(ds: Dataset, average: bool) -> Exercise | None:
    fields = [
        f for f in ds.fields.values()
        if (f.can_average if average else f.can_sum)
        and f.index is not None
        and (not average or f.decimals is None)
    ]
    if not fields:
        return None
    field = random.choice(fields)
    values = [_num(r[field.name]) for r in ds.records]
    if average:
        raw_result = sum(values) / len(values)
        result = int(raw_result * 100 + 0.5) / 100
        title = "Average a numeric field"
        prompt = f'From "{ds.primary_file}", print the average {field.label} across all data rows, rounded to 2 decimal places.'
        solution = f"{_awk_prefix(ds)} '{('NR>'+str(ds.header_rows)+' ' if ds.header_rows else '')}{{sum += {_awk_field_expr(field, True)}; n++}} END {{v=int((sum/n)*100+0.5)/100; printf \"%.2f\\n\", v}}' {ds.primary_file}"
        explanation = "Accumulate the field into `sum`, count rows in `n`, then divide in `END` and round to two decimal places."
        template = "average"
    else:
        result = sum(values)
        title = "Sum a numeric field"
        prompt = f'From "{ds.primary_file}", print the total {field.label} across all data rows, rounded to 2 decimal places.'
        solution = f"{_awk_prefix(ds)} '{('NR>'+str(ds.header_rows)+' ' if ds.header_rows else '')}{{sum += {_awk_field_expr(field, True)}}} END {{printf \"%.2f\\n\", sum+0}}' {ds.primary_file}"
        explanation = "Accumulate the numeric field into a variable and print it once in `END`."
        template = "sum"
    return make(
        ds,
        f"dynamic.{ds.kind}.{template}.{field.name}",
        title,
        prompt,
        "focused",
        ["awk"],
        [skill("awk.variables_end"), skill("awk.fields", "prerequisite")],
        out("ONE NUMBER", "1234.50", "Print exactly one number with 2 decimal places."),
        f"{result:.2f}",
        solution,
        explanation,
    )


def _multi_condition(ds: Dataset, json_mode: bool) -> Exercise | None:
    first = _choose_filter(ds)
    if not first:
        return None
    second = _choose_filter(ds, {first.field.name})
    if not second:
        return None
    matches = [
        r for r in ds.records
        if _match(first.field, first.op, r[first.field.name], first.value)
        and _match(second.field, second.op, r[second.field.name], second.value)
    ]
    if not matches or len(matches) == len(ds.records):
        return None
    outputs = _choose_output_fields(ds, {first.field.name, second.field.name}, allow_two=not json_mode)
    if not outputs:
        return None
    if json_mode:
        output_field = outputs[0]
        expected = "\n".join(_display(output_field, r[output_field.name]) for r in matches)
        cond = f"({_jq_condition(first)}) and ({_jq_condition(second)})"
        solution = f"jq -r 'select({cond}) | .{output_field.name}' {ds.primary_file}"
        tools = ["jq"]
        skills = [skill("jq.select"), skill("jq.field", "reinforcement"), skill("jq.raw", "reinforcement")]
        label = output_field.label
        example = output_field.example
    else:
        expected = _expected_rows(matches, outputs)
        c1 = _awk_condition(ds, first).removeprefix(_header_clause(ds))
        c2 = _awk_condition(ds, second).removeprefix(_header_clause(ds))
        condition = _header_clause(ds) + f"({c1}) && ({c2})"
        print_expr = ", ".join(f"${x.index}" for x in outputs)
        solution = f"{_awk_prefix(ds)} '{condition} {{print {print_expr}}}' {ds.primary_file}"
        tools = ["awk"]
        skills = [skill("awk.conditions"), skill("awk.fields", "reinforcement")]
        if ds.format in ("csv", "colon"):
            skills.append(skill("awk.separator", "reinforcement"))
        label = _field_label(outputs)
        example = _output_example(outputs)
    return make(
        ds,
        f"dynamic.{ds.kind}.multi_filter.{first.field.name}.{second.field.name}.{label.replace(' ', '_')}",
        "Combine two filters",
        f'From "{ds.primary_file}", print {label} for records where {first.prompt} AND {second.prompt}. Preserve input order.',
        "integration",
        tools,
        skills,
        out(label, example, "Both conditions must be true.", "Preserve input order."),
        expected,
        solution,
        "Combine two independent conditions with AND, then print the requested field or fields.",
    )



def _filtered_top_group(ds: Dataset, json_mode: bool) -> Exercise | None:
    choice = _choose_filter(ds)
    if not choice:
        return None
    group_fields = [
        field for field in ds.fields.values()
        if field.can_group and field.can_output and field.name != choice.field.name
    ]
    random.shuffle(group_fields)
    for field in group_fields:
        counts = Counter(_display(field, r[field.name]) for r in choice.matches)
        if len(counts) < 2:
            continue
        winner_value, winner_count = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        expected = f"{winner_count} {winner_value}"
        if json_mode:
            condition = _jq_condition(choice)
            extract = f"jq -r 'select({condition}) | .{field.name}' {ds.primary_file}"
            tools = ["jq", "sort", "uniq", "head", "awk"]
            skills = [
                skill("sort.multiple_keys"),
                skill("uniq.count", "reinforcement"),
                skill("jq.select", "reinforcement"),
                skill("shell.pipeline.multi", "reinforcement"),
            ]
        else:
            condition = _awk_condition(ds, choice)
            extract = f"{_awk_prefix(ds)} '{condition} {{print ${field.index}}}' {ds.primary_file}"
            tools = ["awk", "sort", "uniq", "head"]
            skills = [
                skill("sort.multiple_keys"),
                skill("uniq.count", "reinforcement"),
                skill("awk.conditions", "reinforcement"),
                skill("shell.pipeline.multi", "reinforcement"),
            ]
        solution = extract + " | sort | uniq -c | sort -k1,1nr -k2,2 | head -1 | awk '{print $1, $2}'"
        return make(
            ds,
            f"dynamic.{ds.kind}.challenge_top.{choice.field.name}.{field.name}",
            "Find the dominant value",
            f'Within "{ds.primary_file}", consider only records where {choice.prompt}. Identify the most frequent {field.label} and print `COUNT {field.label}`. Break ties using normal text order.',
            "challenge",
            tools,
            skills,
            out(f"COUNT {field.label}", f"7 {field.example}", "Print exactly one line.", "Count first, then value.", "Break equal counts using normal text order."),
            expected,
            solution,
            "Filter to the relevant records, extract the grouping field, count duplicate values, rank the counts, and keep the top result.",
        )
    return None

def build_dynamic_exercises(ds: Dataset) -> list[Exercise]:
    """Create compositional exercise candidates from dataset field metadata.

    The adaptive engine still chooses *which skill* is appropriate. These recipes
    make the presentation of that skill unpredictable: filter field, operator,
    value, output field, output shape and dataset all vary independently within
    validity constraints.
    """
    if not ds.primary_file or not ds.fields or not ds.records:
        return []

    json_mode = ds.format == "jsonl"
    tabular = ds.format in {"csv", "whitespace", "colon"}
    if not json_mode and not tabular:
        return []

    builders: list[Callable[[], Exercise | None]] = []
    if json_mode:
        builders.extend([
            lambda: _json_filter_project(ds),
            lambda: _json_count_filter(ds),
            lambda: _json_unique(ds),
            lambda: _group_count_common(ds, True),
            lambda: _range_project(ds, True),
            lambda: _multi_condition(ds, True),
            lambda: _filtered_top_group(ds, True),
        ])
    else:
        builders.extend([
            lambda: _tabular_filter_project(ds),
            lambda: _tabular_count_filter(ds),
            lambda: _tabular_unique(ds),
            lambda: _group_count_common(ds, False),
            lambda: _range_project(ds, False),
            lambda: _multi_condition(ds, False),
            lambda: _tabular_sum_or_average(ds, False),
            lambda: _tabular_sum_or_average(ds, True),
            lambda: _filtered_top_group(ds, False),
        ])

    exercises = []
    seen = set()
    for builder in builders:
        # Retry a few times because randomized parameters can legitimately produce
        # empty/all-row/otherwise-degenerate candidates.
        candidate = None
        for _ in range(8):
            candidate = builder()
            if candidate is not None:
                break
        if candidate and candidate.template_id not in seen:
            seen.add(candidate.template_id)
            exercises.append(candidate)
    return exercises
