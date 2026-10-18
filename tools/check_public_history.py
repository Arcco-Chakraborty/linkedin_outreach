"""Check reachable history and public examples without displaying file contents."""
import csv
import io
import json
import pathlib
import re
import subprocess
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def private_path(path):
    parts = path.split("/")
    return (
        any(part == ".env" for part in parts)
        or path == "linkedin_cookies.json"
        or "__pycache__" in parts
        or ".pyc" in path
        or path.endswith(".log")
        or any(part.startswith("output") for part in parts[:-1])
        or path.endswith(".csv") and not path.startswith("examples/")
    )


def reserved_domain(domain):
    return domain in {"example.com", "example.org", "example.net", "probe.local"} or domain.endswith((".example", ".test", ".invalid"))


def check():
    errors = Counter()
    commits = git("rev-list", "--all").splitlines()
    paths = set()
    for commit in commits:
        tree = git("ls-tree", "-r", "--name-only", commit.decode()).decode()
        paths.update(tree.splitlines())
    errors["private_runtime_paths"] = sum(private_path(path) for path in paths)
    objects = git("rev-list", "--objects", "--all").splitlines()
    ids = [entry.split(b" ", 1)[0] for entry in objects]
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "--batch"],
        input=b"\n".join(ids) + b"\n", capture_output=True, check=True,
    )
    offset = blob_count = 0
    for entry in objects:
        end = proc.stdout.index(b"\n", offset)
        header = proc.stdout[offset:end].split()
        offset = end + 1
        size = int(header[2])
        data = proc.stdout[offset:offset + size]
        offset += size + 1
        if header[1] != b"blob":
            continue
        blob_count += 1
        errors["binary_blobs"] += int(b"\0" in data)
        errors["lfs_pointers"] += int(data.startswith(b"version https://git-lfs.github.com/spec/v1"))
        text = data.decode("utf-8", "replace")
        domains = re.findall(r"[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})", text, re.I)
        errors["non_example_contacts"] += sum(not reserved_domain(domain) for domain in domains)
        errors["personal_absolute_paths"] += int(bool(re.search(r"(?<!\w)[A-Za-z]:[\\/]", text)))
    identities = git("log", "--all", "--format=%ae%n%ce").decode().splitlines()
    errors["personal_author_contacts"] = sum(not email.endswith("@users.noreply.github.com") for email in identities)
    messages = git("log", "--all", "--format=%B").decode()
    errors["tool_attribution"] = len(re.findall(r"(?im)^Co-Authored-By:.*(?:Claude|Codex|Anthropic|OpenAI)|^.*Generated (?:with|by).*(?:Claude|Codex|Anthropic|OpenAI)", messages))
    errors["populated_cookie_example"] = int(json.loads((ROOT / "linkedin_cookies.example.json").read_text()) != [])
    env_lines = (ROOT / ".env.example").read_text().splitlines()
    keys = dict(line.split("=", 1) for line in env_lines if line.strip() and not line.startswith("#"))
    errors["populated_apollo_example"] = int(keys.get("APOLLO_API_KEYS") != "")
    for path in (ROOT / "examples").glob("*.csv"):
        for row in csv.DictReader(io.StringIO(path.read_text())):
            if row.get("Email"):
                errors["non_example_csv_contacts"] += int(not reserved_domain(row["Email"].rsplit("@", 1)[1]))
    failures = {key: count for key, count in errors.items() if count}
    print(json.dumps({"passed": not failures, "commits": len(commits), "historical_paths": len(paths), "blobs": blob_count, "findings": failures}, indent=2))
    return not failures


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
