# Console Chaos

Console Chaos is a local Dockerized Linux command trainer. It gives you randomized logs/files, a real Debian practice terminal, a separate pristine grading workspace, persistent JSON history, and an adaptive command-line curriculum.

## Current learning model

Exercises are selected progressively while their concrete data stays randomized:

- **Focused** — teaches/reinforces specific concepts. Final answers are **restricted to the listed tools** and must demonstrate the target concept(s).
- **Integration** — combines concepts. The listed tools are suggestions; alternate valid shell solutions are accepted.
- **Challenge** — open-ended troubleshooting. Correct stdout matters more than the technique used.

There is no global star difficulty. Progress is tracked per concept, for example:

```text
awk.fields
awk.conditions
awk.variables_end
awk.dynamic_fields
sort.multiple_keys
grep.regex
shell.pipeline.multi
```

The selector derives your current frontier from solved `history.json` records and keeps older skills in rotation while introducing harder ones gradually.

## New in this build

- **20 dataset families** now rotate through the trainer, including HTTP CSV, nginx, SSH auth, application logs, JSONL, process/disk data, systemd journal exports, Docker JSONL, Kubernetes events, Slurm jobs, iostat, vmstat, socket tables, DNS records, firewall traffic, config/filesystem data, and more.
- **Field-level randomization**: schema-aware exercises can randomly choose the filter field, operator, filter value, output field(s), grouping field, numeric range, and output shape.
- **Task grammar** now generates filter/project, count, unique, frequency-table, range, sum, average, multi-condition, and filtered top-value exercises from field metadata instead of relying only on handwritten question templates.
- Generated candidates are quality-checked so empty/all-row degenerate questions are retried automatically.
- The adaptive selector now also penalizes recently repeated dataset families, so variety comes from both commands **and** data domains.
- **Split-screen practice workspace**: problem/reference pane on the left, large Debian terminal on the right.
- The left pane uses **Problem / Files / Help / Review** tabs, so long logs no longer push the terminal down the page.
- The answer command is in a **persistent bottom dock** and stays available while you work.
- After a correct answer, a **Next exercise →** button appears directly in the bottom dock.
- The post-solve command history and demonstrated skills live in the Review tab instead of creating a long page below the terminal.
- Desktop uses roughly a **40/60 problem-to-terminal split**; smaller screens fall back to a stacked layout.
- **Output format moved directly under the prompt** so the task reads in a natural order.
- Output examples are explicitly labeled **Format example** and use fake data rather than the answer.
- **Two grading modes**:
  - Focused = restricted tools + target-concept validation.
  - Integration/Challenge = open solution; alternate approaches are welcome.
- Console Chaos now distinguishes:
  - **Exercise focus** (what the template intended to teach)
  - **Skills demonstrated by your accepted command** (what your command actually used)
- The Skills page and adaptive selector now use **demonstrated skills**, not merely the reference solution's concepts.
- Existing history is re-analysed from saved accepted commands so older records do not automatically receive credit for concepts they did not demonstrate.
- **Concept help** is available during an exercise in three progressive stages:
  1. Concept explanation
  2. Syntax + unrelated generic example
  3. Stronger conceptual hint
- Help usage is saved with a solved exercise but is **not treated as a penalty**.
- Introduced skills also show their concept reference on the **Skills** page.
- HTTP/nginx/auth log timestamps now progress forward realistically.
- Terminal output is still never persisted; only command + exit code are saved.
- No database. Persistent state remains a small JSON file.

## Run

From the project directory:

```powershell
docker compose down
docker compose up --build
```

Open:

```text
http://127.0.0.1:5000
```

## Keep existing history

If you are upgrading your existing project, replace the files **inside the same project directory** and use normal `down` / `up --build` commands.

Do **not** run:

```powershell
docker compose down -v
```

unless you intentionally want to erase the persistent volumes, including `/data/history.json`.

The Compose volume keys intentionally remain `shellgym-*` for compatibility with the previous project version.

## Architecture

```text
Browser
   ↓
Console Chaos Flask container
   ↓ private Unix socket
Debian sandbox container
   ├─ /workspace/play
   └─ /workspace/grade
```

The sandbox runs as an unprivileged `student`, has no network, drops Linux capabilities, uses `no-new-privileges`, and has memory/PID/command-time limits.

## Important files

```text
web/exercises/skills.py           curriculum + mastery calculation
web/exercises/concept_help.py     concept documentation / hints
web/exercises/command_analysis.py final-command tool + concept analysis
web/exercises/tasks.py            exercise templates + output contracts
web/exercises/datasets.py         20 randomized dataset families + field schemas
web/exercises/dynamic_tasks.py    metadata-driven task grammar
web/exercises/engine.py           adaptive selector + dataset-variety balancing
web/templates/skills.html         skill-tree UI
```

## Progress states

```text
Not introduced -> Introduced -> Learning -> Practiced -> Comfortable
```

Exploration is not punished. The number of terminal commands you try does not reduce progress. The important evidence is the accepted command and the concepts Console Chaos can confidently identify in it.

## Resizable workspace

On desktop, drag the divider between the problem and terminal to resize the 40/60 split.
Drag the handle at the top of the answer panel to change its height. Both sizes are saved
in browser local storage. The answer panel also has a **Collapse / Expand** button and the
terminal header has **Reset layout**.

Focused answers that use forbidden tools are still executed against the fresh grading files.
Console Chaos tells you separately whether the output itself was correct and whether the
method is allowed for that Focused exercise. Restricted-but-correct answers do not advance
that focused skill until you solve it with the required technique.
