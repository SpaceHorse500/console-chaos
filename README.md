# Console Chaos

Console Chaos is a local, Dockerized Linux command trainer. It gives you randomized files and logs, a real Debian practice terminal, a separate grading workspace, persistent JSON history, and now an adaptive skill curriculum.

## What changed in this version

- Renamed the app from **ShellGym** to **Console Chaos**.
- Removed the star difficulty UI.
- Every exercise is now one of:
  - **Focused** — introduces or reinforces a specific concept.
  - **Integration** — combines multiple already-seen tools/concepts.
  - **Challenge** — open-ended troubleshooting with less hand-holding.
- Every exercise includes a **Desired output** contract with a fake example and formatting rules.
- Exercise templates declare structured skills such as:
  - `awk.fields`
  - `awk.conditions`
  - `awk.dynamic_fields`
  - `sort.multiple_keys`
  - `grep.regex`
  - `shell.pipeline.multi`
- Exercise selection is now **progressive rather than globally random**:
  - new ready concepts are introduced with focused exercises;
  - learning concepts are reinforced;
  - integration exercises appear once prerequisites have been seen;
  - challenges appear later;
  - concrete datasets and thresholds remain randomized.
- New **Skills** page shows a skill tree derived from `history.json`.
- Old history records that do not have skill metadata are interpreted using their saved tools and accepted command, so existing history can still contribute to the tree.
- No database. History remains a small JSON file.
- Terminal output is never persisted; only command + exit code are saved.
- Current curriculum: **37 tracked skills**, **50 exercise templates**, and **11 randomized dataset families**.
- The selector keeps old concepts in rotation while gradually unlocking higher-level AWK, grep, sort, sed, find, jq, wc, head/tail, cut, uniq, redirection, and pipeline concepts.

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

## Important if you want to keep your existing history

If you are upgrading an existing ShellGym folder, replace the project files **inside the same project directory** and run the normal commands above.

Do **not** use:

```powershell
docker compose down -v
```

because `-v` deletes the Docker volumes, including `/data/history.json`.

The Compose volume keys intentionally remain named `shellgym-*` internally for upgrade compatibility. The visible application and container names are Console Chaos.

## Architecture

```text
Browser
   ↓
Console Chaos Flask container
   ↓ Unix socket
Debian sandbox container
   ├─ /workspace/play
   └─ /workspace/grade
```

The sandbox still runs as an unprivileged `student`, has no network, drops Linux capabilities, uses `no-new-privileges`, and has resource/time limits.

## Curriculum files

The key files are:

```text
web/exercises/skills.py   # curriculum + mastery calculation + legacy inference
web/exercises/tasks.py    # exercise templates, skill metadata, output contracts
web/exercises/engine.py   # adaptive/progressive selector
web/templates/skills.html # skill-tree UI
```

Add a new concept to `skills.py`, reference its ID from templates in `tasks.py`, and the Skills page/progression selector will pick it up automatically.

## Progression model

Console Chaos does not use a global star difficulty anymore. It chooses from three exercise styles:

- **Focused**: introduce or reinforce a specific concept.
- **Integration**: combine concepts that have already started to become familiar.
- **Challenge**: open-ended incident-style work after the core concepts have been integrated.

Concrete file contents, thresholds, IPs, services, and log rows remain randomized. In other words, the **skill selection is controlled, but the practice data stays random**.

The Skills page derives progress from `history.json` and uses these states:

```text
Not introduced -> Introduced -> Learning -> Practiced -> Comfortable
```

Every exercise also contains a **Desired output** box with a fake example, so the required stdout shape is clear without revealing the real answer.
