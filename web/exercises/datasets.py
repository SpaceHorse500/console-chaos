from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from .models import Dataset, FieldSpec

WORDS = ["kernel", "network", "linux", "process", "disk", "server", "memory", "daemon", "socket", "system", "cloud", "backup"]
USERS = ["alice", "bob", "carol", "dave", "erin"]
SERVICES = ["api", "worker", "auth", "billing", "search"]
IPS = ["10.0.0.4", "10.0.0.8", "10.0.0.12", "192.168.1.7", "172.16.0.9"]
PATHS = ["/", "/login", "/api/users", "/api/orders", "/api/search", "/health", "/static/app.js"]
HOSTS = ["web-01", "web-02", "db-01", "worker-01", "cache-01"]
REGIONS = ["eu-west", "eu-central", "us-east", "ap-south"]


def lines(items) -> str:
    return "\n".join(map(str, items)) + "\n"


def f(name, label, index=None, *, type="text", role="categorical", operators=("==", "!="),
      can_filter=True, can_output=True, can_group=True, can_sum=False, can_average=False,
      output_suffix="", example="value", decimals=None) -> FieldSpec:
    return FieldSpec(
        name=name,
        label=label,
        index=index,
        type=type,
        role=role,
        operators=tuple(operators),
        can_filter=can_filter,
        can_output=can_output,
        can_group=can_group,
        can_sum=can_sum,
        can_average=can_average,
        output_suffix=output_suffix,
        example=example,
        decimals=decimals,
    )


# ---------------------------------------------------------------------------
# Existing families
# ---------------------------------------------------------------------------

def words_dataset() -> Dataset:
    values = [random.choice(WORDS) for _ in range(random.randint(24, 50))]
    numbers = [random.randint(1, 999) for _ in range(random.randint(14, 24))]
    return Dataset(
        kind="words",
        title="Simple text files",
        files={
            "notes.txt": " ".join(values) + "\n",
            "words.txt": lines(values),
            "numbers.txt": lines(numbers),
        },
        records=[{"value": value} for value in values],
    )


def users_dataset() -> Dataset:
    values = [random.choice(USERS) for _ in range(random.randint(25, 50))]
    return Dataset(
        kind="users",
        title="User list",
        files={
            "users.txt": lines(values),
            "users_sorted.txt": lines(sorted(values)),
        },
        records=[{"user": value} for value in values],
    )


def requests_csv_dataset() -> Dataset:
    rows = ["ts,ip,method,path,status,bytes,duration_ms"]
    records = []
    current = datetime(2026, 9, 14, 1, 0, 0)
    total = random.randint(32, 58)
    forced_statuses = [200, 404, 500, 502]
    for i in range(total):
        r = {
            "ts": current.strftime("%H:%M:%S"),
            "ip": random.choice(IPS),
            "method": random.choice(["GET", "GET", "GET", "POST", "PUT", "DELETE"]),
            "path": random.choice(PATHS),
            "status": forced_statuses[i] if i < len(forced_statuses) else random.choice([200, 200, 200, 201, 301, 400, 401, 403, 404, 429, 500, 502, 503]),
            "bytes": random.randint(80, 18000),
            "duration_ms": random.randint(5, 1800),
        }
        records.append(r)
        rows.append(f'{r["ts"]},{r["ip"]},{r["method"]},{r["path"]},{r["status"]},{r["bytes"]},{r["duration_ms"]}')
        current += timedelta(seconds=random.randint(2, 7))
    return Dataset(
        "requests_csv", "HTTP request CSV", {"requests.csv": lines(rows)}, records,
        primary_file="requests.csv", format="csv", delimiter=",", header_rows=1,
        fields={
            "ip": f("ip", "IP", 2, role="identifier", example="203.0.113.42"),
            "method": f("method", "METHOD", 3, example="POST"),
            "path": f("path", "PATH", 4, example="/api/items"),
            "status": f("status", "STATUS", 5, type="number", role="categorical", operators=("==", "!=", ">=", "<="), example="404"),
            "bytes": f("bytes", "BYTES", 6, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="8192"),
            "duration_ms": f("duration_ms", "DURATION_MS", 7, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="725"),
        },
    )


def nginx_dataset() -> Dataset:
    rows, records = [], []
    current = datetime(2026, 9, 14, 1, 15, 0)
    total = random.randint(32, 58)
    forced_statuses = [404, 500, 502]
    for i in range(total):
        r = {
            "ip": random.choice(IPS),
            "ts": current.strftime("%d/%b/%Y:%H:%M:%S +0000"),
            "method": random.choice(["GET", "GET", "GET", "POST"]),
            "path": random.choice(PATHS),
            "status": forced_statuses[i] if i < len(forced_statuses) else random.choice([200, 200, 200, 301, 400, 401, 404, 429, 500, 502]),
            "bytes": random.randint(100, 15000),
            "duration_ms": random.randint(4, 1800),
        }
        records.append(r)
        rows.append(f'{r["ip"]} - - [{r["ts"]}] "{r["method"]} {r["path"]} HTTP/1.1" {r["status"]} {r["bytes"]} {r["duration_ms"]}ms')
        current += timedelta(seconds=random.randint(1, 5))
    return Dataset("nginx", "nginx access log", {"access.log": lines(rows)}, records)


def auth_dataset() -> Dataset:
    rows, records = [], []
    current = datetime(2026, 9, 14, 1, 0, 0)
    for row_index in range(random.randint(30, 55)):
        success = False if row_index < 2 else random.random() < 0.35
        user, ip = random.choice(USERS), random.choice(IPS)
        pid = random.randint(1000, 9999)
        ts = current.strftime("%b %d %H:%M:%S")
        current += timedelta(seconds=random.randint(4, 45))
        if success:
            msg = f"{ts} server sshd[{pid}]: Accepted publickey for {user} from {ip} port {random.randint(20000,60000)} ssh2"
            outcome = "accepted"
        else:
            if random.random() < 0.30:
                msg = f"{ts} server sshd[{pid}]: Failed password for invalid user {user} from {ip} port {random.randint(20000,60000)} ssh2"
            else:
                msg = f"{ts} server sshd[{pid}]: Failed password for {user} from {ip} port {random.randint(20000,60000)} ssh2"
            outcome = "failed"
        rows.append(msg)
        records.append({"user": user, "ip": ip, "outcome": outcome, "line": msg})
    return Dataset("auth", "SSH authentication log", {"auth.log": lines(rows)}, records)


def app_kv_dataset() -> Dataset:
    rows, records = [], []
    start = datetime(2026, 9, 14, 1, 30, 0)
    for i in range(random.randint(32, 58)):
        r = {
            "ts": (start + timedelta(seconds=i * 3)).isoformat(),
            "level": "ERROR" if i == 0 else random.choice(["INFO", "INFO", "INFO", "WARN", "ERROR"]),
            "service": random.choice(SERVICES),
            "user": random.choice(USERS),
            "duration_ms": random.randint(5, 1800),
            "status": random.choice(["ok", "ok", "ok", "retry", "failed"]),
        }
        records.append(r)
        # Occasionally vary key order so later exercises cannot always hard-code $3.
        pairs = [
            f'level={r["level"]}', f'service={r["service"]}', f'user={r["user"]}',
            f'duration_ms={r["duration_ms"]}', f'status={r["status"]}',
        ]
        if random.random() < 0.28:
            random.shuffle(pairs)
        rows.append(r["ts"] + " " + " ".join(pairs))
    return Dataset("app_kv", "Application key=value log", {"app.log": lines(rows)}, records)


def jsonl_dataset() -> Dataset:
    rows, records = [], []
    start = datetime(2026, 9, 14, 2, 0, 0)
    for i in range(random.randint(30, 52)):
        r = {
            "ts": (start + timedelta(seconds=i * 4)).isoformat(),
            "service": random.choice(SERVICES),
            "level": "ERROR" if i == 0 else random.choice(["INFO", "INFO", "WARN", "ERROR"]),
            "status": 500 if i == 0 else random.choice([200, 200, 201, 400, 404, 429, 500]),
            "duration_ms": random.randint(5, 1600),
            "user": random.choice(USERS),
            "region": random.choice(REGIONS),
        }
        records.append(r)
        rows.append(json.dumps(r, separators=(",", ":")))
    return Dataset(
        "jsonl", "JSON-lines application events", {"events.jsonl": lines(rows)}, records,
        primary_file="events.jsonl", format="jsonl", header_rows=0,
        fields={
            "service": f("service", "SERVICE", role="categorical", example="api"),
            "level": f("level", "LEVEL", role="categorical", example="ERROR"),
            "status": f("status", "STATUS", type="number", role="categorical", operators=("==", "!=", ">=", "<="), example="500"),
            "duration_ms": f("duration_ms", "DURATION_MS", type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="850"),
            "user": f("user", "USER", role="identifier", example="alice"),
            "region": f("region", "REGION", role="categorical", example="eu-west"),
        },
    )


def ps_dataset() -> Dataset:
    commands = [
        "/usr/bin/python3", "/usr/sbin/nginx", "/usr/bin/redis-server",
        "/usr/bin/postgres", "/usr/bin/java", "/usr/bin/node",
        "/usr/bin/prometheus", "/usr/bin/grafana-server",
    ]
    rows = ["USER PID %CPU %MEM COMMAND"]
    records = []
    for i, command in enumerate(commands, 1):
        r = {
            "user": random.choice(["root", "www-data", "postgres", "app"]),
            "pid": 900 + i * random.randint(7, 19),
            "cpu": round(random.uniform(0.1, 95.0), 1),
            "mem": round(random.uniform(0.1, 35.0), 1),
            "command": command,
        }
        records.append(r)
        rows.append(f'{r["user"]} {r["pid"]} {r["cpu"]:.1f} {r["mem"]:.1f} {r["command"]}')
    return Dataset(
        "ps", "Simulated process list", {"processes.txt": lines(rows)}, records,
        primary_file="processes.txt", format="whitespace", header_rows=1,
        fields={
            "user": f("user", "USER", 1, role="identifier", example="app"),
            "pid": f("pid", "PID", 2, type="number", role="identifier", operators=("==", "!=", ">", "<"), can_group=False, example="1432"),
            "cpu": f("cpu", "%CPU", 3, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="72.4", decimals=1),
            "mem": f("mem", "%MEM", 4, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="18.6", decimals=1),
            "command": f("command", "COMMAND", 5, role="categorical", can_filter=False, example="/usr/sbin/nginx"),
        },
    )


def df_dataset() -> Dataset:
    mounts = [("/dev/sda1", "/", 100), ("/dev/sdb1", "/var", 80), ("/dev/sdc1", "/home", 200), ("/dev/sdd1", "/data", 500), ("tmpfs", "/run", 16)]
    rows = ["Filesystem SizeG UsedG AvailG Use% Mounted_on"]
    records = []
    for filesystem, mount, size in mounts:
        percent = random.randint(15, 97)
        used = round(size * percent / 100)
        r = {"filesystem": filesystem, "size": size, "used": used, "avail": max(size-used,0), "percent": percent, "mount": mount}
        records.append(r)
        rows.append(f'{filesystem} {size} {r["used"]} {r["avail"]} {percent}% {mount}')
    return Dataset(
        "df", "Simulated disk usage", {"df.txt": lines(rows)}, records,
        primary_file="df.txt", format="whitespace", header_rows=1,
        fields={
            "filesystem": f("filesystem", "FILESYSTEM", 1, role="identifier", example="/dev/sdb1"),
            "size": f("size", "SIZE_G", 2, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="200"),
            "used": f("used", "USED_G", 3, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="160"),
            "avail": f("avail", "AVAIL_G", 4, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="40"),
            "percent": f("percent", "USE%", 5, type="number", role="metric", operators=(">", "<", ">=", "<="), output_suffix="%", example="82%"),
            "mount": f("mount", "MOUNT", 6, role="identifier", example="/var"),
        },
    )


def config_dataset() -> Dataset:
    keys = [("PORT", str(random.choice([8080,8081,9000]))), ("WORKERS", str(random.randint(2,12))), ("LOG_LEVEL", random.choice(["INFO","WARN","ERROR"])), ("CACHE", random.choice(["true","false"])), ("TIMEOUT", str(random.randint(10,90)))]
    rows = ["# service configuration", ""]
    active = []
    for key, value in keys:
        if random.random() < 0.6:
            rows.append(f"# setting for {key}")
        line = f"{key}={value}"
        rows.append(line)
        active.append(line)
        if random.random() < 0.4:
            rows.append("")
    return Dataset("config", "Configuration file", {"service.conf": lines(rows)}, [{"line": x} for x in active])


def filetree_dataset() -> Dataset:
    files = {
        "logs/app.log": "application\n",
        "logs/nginx/access.log": "access\n",
        "logs/nginx/error.log": "error\n",
        "logs/archive/app-1.log": "old\n",
        "data/users.csv": "id,user\n1,alice\n",
        "data/events.json": '{"ok":true}\n',
        "README.txt": "training\n",
    }
    return Dataset("filetree", "Directory tree", files, [{"path": p} for p in files])


# ---------------------------------------------------------------------------
# New dataset families (20 total families in the application)
# ---------------------------------------------------------------------------

def journal_dataset() -> Dataset:
    units = ["nginx.service", "api.service", "postgresql.service", "worker.service", "ssh.service"]
    priorities = ["INFO", "INFO", "WARNING", "ERROR"]
    events = ["started", "request_failed", "timeout", "reloaded", "connection_reset", "healthy"]
    rows = ["TS HOST UNIT PID PRIORITY EVENT"]
    records = []
    current = datetime(2026, 9, 14, 3, 0, 0)
    for _ in range(random.randint(28, 50)):
        r = {
            "ts": current.strftime("%H:%M:%S"), "host": random.choice(HOSTS), "unit": random.choice(units),
            "pid": random.randint(800, 9000), "priority": random.choice(priorities), "event": random.choice(events),
        }
        records.append(r)
        rows.append(f'{r["ts"]} {r["host"]} {r["unit"]} {r["pid"]} {r["priority"]} {r["event"]}')
        current += timedelta(seconds=random.randint(2, 20))
    return Dataset(
        "journal", "systemd journal export", {"journal.txt": lines(rows)}, records,
        primary_file="journal.txt", format="whitespace", header_rows=1,
        fields={
            "host": f("host", "HOST", 2, role="identifier", example="web-01"),
            "unit": f("unit", "UNIT", 3, role="categorical", example="nginx.service"),
            "pid": f("pid", "PID", 4, type="number", role="identifier", operators=("==", "!=", ">", "<"), can_group=False, example="1732"),
            "priority": f("priority", "PRIORITY", 5, role="categorical", example="ERROR"),
            "event": f("event", "EVENT", 6, role="categorical", example="timeout"),
        },
    )


def docker_jsonl_dataset() -> Dataset:
    containers = ["api-1", "api-2", "worker-1", "redis-1", "gateway-1"]
    rows, records = [], []
    current = datetime(2026, 9, 14, 3, 30, 0)
    for _ in range(random.randint(30, 52)):
        r = {
            "ts": current.isoformat(),
            "container": random.choice(containers),
            "stream": random.choice(["stdout", "stdout", "stderr"]),
            "level": random.choice(["INFO", "INFO", "WARN", "ERROR"]),
            "event": random.choice(["request", "job", "retry", "timeout", "healthcheck"]),
            "duration_ms": random.randint(3, 2200),
        }
        records.append(r)
        rows.append(json.dumps(r, separators=(",", ":")))
        current += timedelta(seconds=random.randint(1, 8))
    return Dataset(
        "docker_jsonl", "Docker JSON-lines logs", {"docker.jsonl": lines(rows)}, records,
        primary_file="docker.jsonl", format="jsonl",
        fields={
            "container": f("container", "CONTAINER", role="identifier", example="api-1"),
            "stream": f("stream", "STREAM", example="stderr"),
            "level": f("level", "LEVEL", example="ERROR"),
            "event": f("event", "EVENT", example="timeout"),
            "duration_ms": f("duration_ms", "DURATION_MS", type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="930"),
        },
    )


def k8s_events_dataset() -> Dataset:
    rows = ["namespace,pod,type,reason,restarts,age_s,node"]
    records = []
    namespaces = ["prod", "staging", "monitoring"]
    reasons = ["Started", "BackOff", "Pulled", "Killing", "Unhealthy", "Scheduled"]
    nodes = ["node-a", "node-b", "node-c"]
    for i in range(random.randint(28, 48)):
        r = {
            "namespace": random.choice(namespaces),
            "pod": f'{random.choice(["api","worker","web","cron"])}-{random.randint(1,5)}',
            "type": random.choice(["Normal", "Normal", "Warning"]),
            "reason": random.choice(reasons),
            "restarts": random.randint(0, 12),
            "age_s": random.randint(10, 7200),
            "node": random.choice(nodes),
        }
        records.append(r)
        rows.append(','.join(str(r[k]) for k in ("namespace","pod","type","reason","restarts","age_s","node")))
    return Dataset(
        "k8s_events", "Kubernetes event table", {"k8s_events.csv": lines(rows)}, records,
        primary_file="k8s_events.csv", format="csv", delimiter=",", header_rows=1,
        fields={
            "namespace": f("namespace", "NAMESPACE", 1, example="prod"),
            "pod": f("pod", "POD", 2, role="identifier", example="api-2"),
            "type": f("type", "TYPE", 3, example="Warning"),
            "reason": f("reason", "REASON", 4, example="BackOff"),
            "restarts": f("restarts", "RESTARTS", 5, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="4"),
            "age_s": f("age_s", "AGE_S", 6, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="900"),
            "node": f("node", "NODE", 7, role="identifier", example="node-b"),
        },
    )


def slurm_dataset() -> Dataset:
    rows = ["JOBID USER PARTITION STATE ELAPSED_S NODES CPUS"]
    records = []
    states = ["RUNNING", "RUNNING", "COMPLETED", "FAILED", "PENDING", "CANCELLED"]
    partitions = ["short", "compute", "gpu", "long"]
    for i in range(random.randint(24, 42)):
        r = {
            "jobid": 41000 + i,
            "user": random.choice(USERS),
            "partition": random.choice(partitions),
            "state": random.choice(states),
            "elapsed_s": random.randint(20, 24000),
            "nodes": random.randint(1, 8),
            "cpus": random.choice([1,2,4,8,16,32]),
        }
        records.append(r)
        rows.append(f'{r["jobid"]} {r["user"]} {r["partition"]} {r["state"]} {r["elapsed_s"]} {r["nodes"]} {r["cpus"]}')
    return Dataset(
        "slurm", "Slurm job queue export", {"jobs.txt": lines(rows)}, records,
        primary_file="jobs.txt", format="whitespace", header_rows=1,
        fields={
            "jobid": f("jobid", "JOBID", 1, type="number", role="identifier", operators=("==", "!="), can_group=False, example="41018"),
            "user": f("user", "USER", 2, role="identifier", example="alice"),
            "partition": f("partition", "PARTITION", 3, example="gpu"),
            "state": f("state", "STATE", 4, example="FAILED"),
            "elapsed_s": f("elapsed_s", "ELAPSED_S", 5, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="3600"),
            "nodes": f("nodes", "NODES", 6, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="4"),
            "cpus": f("cpus", "CPUS", 7, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="16"),
        },
    )


def iostat_dataset() -> Dataset:
    rows = ["DEVICE READ_KBPS WRITE_KBPS AWAIT_MS UTIL_PCT"]
    records = []
    for device in ["sda", "sdb", "nvme0n1", "nvme1n1", "dm-0", "dm-1"]:
        r = {
            "device": device,
            "read_kbps": round(random.uniform(0, 9000), 1),
            "write_kbps": round(random.uniform(0, 9000), 1),
            "await_ms": round(random.uniform(0.2, 90), 1),
            "util_pct": round(random.uniform(1, 99), 1),
        }
        records.append(r)
        rows.append(f'{device} {r["read_kbps"]:.1f} {r["write_kbps"]:.1f} {r["await_ms"]:.1f} {r["util_pct"]:.1f}')
    return Dataset(
        "iostat", "iostat device metrics", {"iostat.txt": lines(rows)}, records,
        primary_file="iostat.txt", format="whitespace", header_rows=1,
        fields={
            "device": f("device", "DEVICE", 1, role="identifier", example="nvme0n1"),
            "read_kbps": f("read_kbps", "READ_KBPS", 2, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="4210.5", decimals=1),
            "write_kbps": f("write_kbps", "WRITE_KBPS", 3, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="812.4", decimals=1),
            "await_ms": f("await_ms", "AWAIT_MS", 4, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="18.7", decimals=1),
            "util_pct": f("util_pct", "UTIL_PCT", 5, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="87.2", decimals=1),
        },
    )


def vmstat_dataset() -> Dataset:
    rows = ["R B SWPD FREE BUFF CACHE SI SO BI BO US SY ID WA"]
    records = []
    for _ in range(random.randint(18, 32)):
        r = {
            "r": random.randint(0, 12), "b": random.randint(0, 4), "swpd": random.randint(0, 4096),
            "free": random.randint(500, 32000), "buff": random.randint(50, 2500), "cache": random.randint(500, 18000),
            "si": random.randint(0, 80), "so": random.randint(0, 80), "bi": random.randint(0, 5000), "bo": random.randint(0, 5000),
            "us": random.randint(1, 80), "sy": random.randint(1, 35), "id": random.randint(1, 95), "wa": random.randint(0, 45),
        }
        records.append(r)
        rows.append(" ".join(str(r[k]) for k in ("r","b","swpd","free","buff","cache","si","so","bi","bo","us","sy","id","wa")))
    labels = ["R","B","SWPD","FREE","BUFF","CACHE","SI","SO","BI","BO","US","SY","ID","WA"]
    keys = ["r","b","swpd","free","buff","cache","si","so","bi","bo","us","sy","id","wa"]
    fields = {}
    for idx, (key, label) in enumerate(zip(keys, labels), 1):
        fields[key] = f(key, label, idx, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example=str(random.randint(5, 80)))
    return Dataset(
        "vmstat", "vmstat samples", {"vmstat.txt": lines(rows)}, records,
        primary_file="vmstat.txt", format="whitespace", header_rows=1, fields=fields,
    )


def ss_dataset() -> Dataset:
    rows = ["state,protocol,local_ip,local_port,remote_ip,remote_port,process"]
    records = []
    processes = ["nginx", "sshd", "postgres", "redis", "api"]
    for _ in range(random.randint(28, 50)):
        r = {
            "state": random.choice(["ESTAB", "ESTAB", "LISTEN", "TIME-WAIT", "CLOSE-WAIT"]),
            "protocol": random.choice(["tcp", "tcp", "udp"]),
            "local_ip": random.choice(IPS),
            "local_port": random.choice([22, 80, 443, 5432, 6379, 8080, 9000]),
            "remote_ip": random.choice(IPS),
            "remote_port": random.randint(20000, 65000),
            "process": random.choice(processes),
        }
        records.append(r)
        rows.append(','.join(str(r[k]) for k in ("state","protocol","local_ip","local_port","remote_ip","remote_port","process")))
    return Dataset(
        "ss", "Socket connection table", {"connections.csv": lines(rows)}, records,
        primary_file="connections.csv", format="csv", delimiter=",", header_rows=1,
        fields={
            "state": f("state", "STATE", 1, example="ESTAB"),
            "protocol": f("protocol", "PROTOCOL", 2, example="tcp"),
            "local_ip": f("local_ip", "LOCAL_IP", 3, role="identifier", example="10.0.0.8"),
            "local_port": f("local_port", "LOCAL_PORT", 4, type="number", role="categorical", operators=("==", "!=", ">", "<"), example="443"),
            "remote_ip": f("remote_ip", "REMOTE_IP", 5, role="identifier", example="203.0.113.50"),
            "remote_port": f("remote_port", "REMOTE_PORT", 6, type="number", role="metric", operators=(">", "<", ">=", "<="), can_average=True, example="51520"),
            "process": f("process", "PROCESS", 7, role="categorical", example="nginx"),
        },
    )


def dns_dataset() -> Dataset:
    rows = ["NAME TYPE TTL VALUE"]
    records = []
    names = ["api.example.test", "www.example.test", "db.example.test", "mail.example.test", "cache.example.test"]
    types = ["A", "AAAA", "CNAME", "MX"]
    for _ in range(random.randint(24, 40)):
        typ = random.choice(types)
        if typ == "A":
            value = random.choice(IPS)
        elif typ == "AAAA":
            value = random.choice(["2001:db8::10", "2001:db8::20", "2001:db8::30"])
        elif typ == "MX":
            value = random.choice(["mail1.example.test", "mail2.example.test"])
        else:
            value = random.choice(["edge.example.test", "origin.example.test"])
        r = {"name": random.choice(names), "type": typ, "ttl": random.choice([60, 120, 300, 600, 3600]), "value": value}
        records.append(r)
        rows.append(f'{r["name"]} {r["type"]} {r["ttl"]} {r["value"]}')
    return Dataset(
        "dns", "DNS record export", {"dns.txt": lines(rows)}, records,
        primary_file="dns.txt", format="whitespace", header_rows=1,
        fields={
            "name": f("name", "NAME", 1, role="identifier", example="api.example.test"),
            "type": f("type", "TYPE", 2, example="A"),
            "ttl": f("ttl", "TTL", 3, type="number", role="metric", operators=(">", "<", ">=", "<="), can_average=True, example="300"),
            "value": f("value", "VALUE", 4, role="identifier", example="203.0.113.10"),
        },
    )


def firewall_dataset() -> Dataset:
    rows = ["ts,src_ip,dst_ip,src_port,dst_port,protocol,action,bytes"]
    records = []
    current = datetime(2026, 9, 14, 4, 0, 0)
    for _ in range(random.randint(32, 58)):
        r = {
            "ts": current.strftime("%H:%M:%S"),
            "src_ip": random.choice(IPS), "dst_ip": random.choice(IPS),
            "src_port": random.randint(1024, 65000), "dst_port": random.choice([22,53,80,443,5432,6379,8080]),
            "protocol": random.choice(["TCP", "TCP", "UDP"]),
            "action": random.choice(["ALLOW", "ALLOW", "ALLOW", "DENY"]),
            "bytes": random.randint(40, 24000),
        }
        records.append(r)
        rows.append(','.join(str(r[k]) for k in ("ts","src_ip","dst_ip","src_port","dst_port","protocol","action","bytes")))
        current += timedelta(seconds=random.randint(1, 9))
    return Dataset(
        "firewall", "Firewall traffic log", {"firewall.csv": lines(rows)}, records,
        primary_file="firewall.csv", format="csv", delimiter=",", header_rows=1,
        fields={
            "src_ip": f("src_ip", "SRC_IP", 2, role="identifier", example="203.0.113.42"),
            "dst_ip": f("dst_ip", "DST_IP", 3, role="identifier", example="10.0.0.8"),
            "src_port": f("src_port", "SRC_PORT", 4, type="number", role="metric", operators=(">", "<", ">=", "<="), example="51820"),
            "dst_port": f("dst_port", "DST_PORT", 5, type="number", role="categorical", operators=("==", "!=", ">", "<"), example="443"),
            "protocol": f("protocol", "PROTOCOL", 6, example="TCP"),
            "action": f("action", "ACTION", 7, example="DENY"),
            "bytes": f("bytes", "BYTES", 8, type="number", role="metric", operators=(">", "<", ">=", "<="), can_sum=True, can_average=True, example="4096"),
        },
    )


DATASET_GENERATORS = [
    words_dataset,
    users_dataset,
    requests_csv_dataset,
    nginx_dataset,
    auth_dataset,
    app_kv_dataset,
    jsonl_dataset,
    ps_dataset,
    df_dataset,
    config_dataset,
    filetree_dataset,
    journal_dataset,
    docker_jsonl_dataset,
    k8s_events_dataset,
    slurm_dataset,
    iostat_dataset,
    vmstat_dataset,
    ss_dataset,
    dns_dataset,
    firewall_dataset,
]
