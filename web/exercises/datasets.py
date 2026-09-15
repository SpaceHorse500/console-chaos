from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from .models import Dataset

WORDS = ["kernel", "network", "linux", "process", "disk", "server", "memory", "daemon", "socket", "system", "cloud", "backup"]
USERS = ["alice", "bob", "carol", "dave", "erin"]
SERVICES = ["api", "worker", "auth", "billing", "search"]
IPS = ["10.0.0.4", "10.0.0.8", "10.0.0.12", "192.168.1.7", "172.16.0.9"]
PATHS = ["/", "/login", "/api/users", "/api/orders", "/api/search", "/health", "/static/app.js"]


def lines(items) -> str:
    return "\n".join(map(str, items)) + "\n"


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
    start = datetime(2026, 9, 14, 1, 0, 0)
    total = random.randint(30, 55)
    forced_statuses = [404, 500, 502]
    for i in range(total):
        r = {
            "ts": (start + timedelta(seconds=i * random.randint(2, 7))).strftime("%H:%M:%S"),
            "ip": random.choice(IPS),
            "method": random.choice(["GET", "GET", "GET", "POST", "PUT"]),
            "path": random.choice(PATHS),
            "status": forced_statuses[i] if i < len(forced_statuses) else random.choice([200, 200, 200, 201, 301, 400, 401, 403, 404, 500, 502]),
            "bytes": random.randint(80, 12000),
            "duration_ms": random.randint(5, 1500),
        }
        records.append(r)
        rows.append(f'{r["ts"]},{r["ip"]},{r["method"]},{r["path"]},{r["status"]},{r["bytes"]},{r["duration_ms"]}')
    return Dataset("requests_csv", "HTTP request CSV", {"requests.csv": lines(rows)}, records)


def nginx_dataset() -> Dataset:
    rows, records = [], []
    start = datetime(2026, 9, 14, 1, 15, 0)
    total = random.randint(32, 58)
    forced_statuses = [404, 500, 502]
    for i in range(total):
        r = {
            "ip": random.choice(IPS),
            "ts": (start + timedelta(seconds=i * random.randint(1, 5))).strftime("%d/%b/%Y:%H:%M:%S +0000"),
            "method": random.choice(["GET", "GET", "GET", "POST"]),
            "path": random.choice(PATHS),
            "status": forced_statuses[i] if i < len(forced_statuses) else random.choice([200, 200, 200, 301, 400, 401, 404, 500, 502]),
            "bytes": random.randint(100, 15000),
            "duration_ms": random.randint(4, 1800),
        }
        records.append(r)
        rows.append(f'{r["ip"]} - - [{r["ts"]}] "{r["method"]} {r["path"]} HTTP/1.1" {r["status"]} {r["bytes"]} {r["duration_ms"]}ms')
    return Dataset("nginx", "nginx access log", {"access.log": lines(rows)}, records)


def auth_dataset() -> Dataset:
    rows, records = [], []
    minute = 0
    for row_index in range(random.randint(30, 55)):
        success = False if row_index < 2 else random.random() < 0.35
        user, ip = random.choice(USERS), random.choice(IPS)
        pid = random.randint(1000, 9999)
        minute += random.randint(0, 2)
        ts = f"Sep 14 01:{minute % 60:02d}:{random.randint(0,59):02d}"
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
        rows.append(f'{r["ts"]} level={r["level"]} service={r["service"]} user={r["user"]} duration_ms={r["duration_ms"]} status={r["status"]}')
    return Dataset("app_kv", "Application key=value log", {"app.log": lines(rows)}, records)


def jsonl_dataset() -> Dataset:
    rows, records = [], []
    start = datetime(2026, 9, 14, 2, 0, 0)
    for i in range(random.randint(28, 48)):
        r = {
            "ts": (start + timedelta(seconds=i * 4)).isoformat(),
            "service": random.choice(SERVICES),
            "level": "ERROR" if i == 0 else random.choice(["INFO", "INFO", "WARN", "ERROR"]),
            "status": 500 if i == 0 else random.choice([200, 200, 201, 400, 404, 500]),
            "duration_ms": random.randint(5, 1600),
            "user": random.choice(USERS),
        }
        records.append(r)
        rows.append(json.dumps(r, separators=(",", ":")))
    return Dataset("jsonl", "JSON-lines application events", {"events.jsonl": lines(rows)}, records)


def ps_dataset() -> Dataset:
    commands = [
        "/usr/bin/python3 api.py", "/usr/sbin/nginx", "/usr/bin/redis-server",
        "/usr/bin/postgres", "/usr/bin/java -jar worker.jar", "/usr/bin/node server.js",
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
    return Dataset("ps", "Simulated process list", {"processes.txt": lines(rows)}, records)


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
    return Dataset("df", "Simulated disk usage", {"df.txt": lines(rows)}, records)


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


DATASET_GENERATORS = [words_dataset, users_dataset, requests_csv_dataset, nginx_dataset, auth_dataset, app_kv_dataset, jsonl_dataset, ps_dataset, df_dataset, config_dataset, filetree_dataset]
