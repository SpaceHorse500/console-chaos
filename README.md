# ShellGym v2

ShellGym is a Dockerized Linux command practice lab.

## What this version adds

- **No database.** Solved history is stored in `/data/history.json` on a Docker volume.
- Practice-terminal history stores only:
  - command
  - exit code
- Terminal stdout/stderr is **not persisted**.
- After solving an exercise, the page shows your terminal exploration immediately.
- The History page stores and displays:
  - question
  - generated files
  - suggested tools
  - terminal commands
  - submitted answers
  - accepted answer
  - reference solution
  - explanation
- Exercise generation is split into **datasets + tasks** instead of one hard-coded function per whole exercise.
- Current randomized dataset families:
  - HTTP CSV requests
  - nginx access logs
  - SSH/auth logs
  - key=value application logs
  - JSON-lines events
  - simulated process (`ps`) output
  - simulated disk (`df`) output
  - config files
  - directory trees
  - word/user datasets
- Current exercise families cover filtering, extraction, counting, unique values, sorting, thresholds, aggregation, top offenders, file finding, JSON parsing and multi-command pipelines.
- Detailed reference explanations remain available.
- `man` pages are installed; `man awk` points to GNU awk documentation.

## Architecture

```text
Browser
   |
   v
Flask web container
   |
   | Unix domain socket
   v
Debian sandbox container
   |
   +-- /workspace/play    free experimentation
   +-- /workspace/grade   fresh copy for grading
```

The sandbox runs as unprivileged `student`, has no Docker network, drops all Linux capabilities, uses `no-new-privileges`, and has memory/PID/command-time limits.

## Start

```powershell
docker compose up --build
```

Open:

```text
http://127.0.0.1:5000
```

Stop:

```powershell
docker compose down
```

History survives ordinary rebuilds and `docker compose down` because `/data` is a named volume.

To wipe all persistent ShellGym data including history:

```powershell
docker compose down -v
```

## Useful commands

```powershell
docker compose ps
docker compose logs -f
docker exec -it shellgym-sandbox bash
```

## Help inside ShellGym

```bash
awk --help
grep --help
man awk
man grep
man sed
man wc
```

Because the browser terminal is not a true TTY, ShellGym sets `MANPAGER=cat` and `PAGER=cat` so manual pages print directly in the web terminal.
