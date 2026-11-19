#!/usr/bin/env python3
"""Index skill and command metadata without running the discovered files."""

import argparse
import hashlib
from itertools import islice
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
from contextlib import closing
from datetime import datetime, timezone

MAX_ENTRIES = 3000
MAX_PATHS = 12000
MAX_DEPTH = 6
MAX_HEADER = 24 * 1024
MAX_BODY = 128 * 1024

EXCLUDED = {"node_modules", "vendor", "vendors", "dist", "build", "__pycache__", "target", "archive", "archives",
            "assets", "examples", "references", "resources", "scripts", "tests"}
MARKERS = (".git", "AGENTS.md", "CLAUDE.md", ".agents", ".codex", ".claude")
FIELDS = {"name", "description", "trigger", "triggers", "aliases", "related"}
STOP = set("a an and are can for from how i in is it me my of on or our run the this to use want what when where which with you".split())
WEAK = set("advice app automation basic best build check setup create example file find get guide help look make new open plan recommend review show skill support task tool type up update work one two three four five six seven eight nine ten".split())
ROUTERS = {"meta-h", "su-meta-h"}
CONCEPTS = (
    ("mac", "macos", "disk", "storage", "swap", "ram", "memory pressure", "slow computer", "health check"),
    ("chief of staff", "daily brief", "prioritize", "priorities", "commitments", "handoff", "agenda", "workday"),
    ("pull request", "pr", "code review", "merge request", "review branch"),
    ("calendar", "availability", "schedule", "meeting", "appointment"),
    ("image", "screenshot", "visual", "mockup", "illustration"),
    ("email", "mail", "inbox", "recipient", "reply"),
    ("publish", "deploy", "release", "ship", "rollout"),
    ("skill discovery", "skill catalog", "find skill", "skill search", "which skill"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS scopes (
    scope TEXT PRIMARY KEY,
    synced_at TEXT NOT NULL,
    truncated INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS roots (
    scope TEXT NOT NULL,
    path TEXT NOT NULL,
    PRIMARY KEY (scope, path)
);
CREATE TABLE IF NOT EXISTS aliases (
    scope TEXT NOT NULL,
    phrase TEXT NOT NULL,
    path TEXT NOT NULL,
    PRIMARY KEY (scope, phrase)
);
CREATE TABLE IF NOT EXISTS entries (
    scope TEXT NOT NULL,
    id TEXT NOT NULL,
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    path TEXT NOT NULL,
    target TEXT NOT NULL,
    root TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    triggers TEXT NOT NULL,
    aliases TEXT NOT NULL,
    related TEXT NOT NULL,
    PRIMARY KEY (scope, id)
);
"""


def under(path, parent):
    return path == parent or parent in path.parents


def is_project(path):
    return any((path / marker).exists() for marker in MARKERS)


def project_for(cwd, home):
    for path in (cwd, *cwd.parents):
        if path in (home, Path(path.anchor)):
            break
        if is_project(path):
            return path
    return cwd


def config_root(variable, default):
    value = os.environ.get(variable)
    return absolute(value).resolve() if value else default


def absolute(value):
    return Path(os.path.abspath(Path(value).expanduser()))


def root_specs(project, home, extra):
    roots = []
    if project not in (home, Path(project.anchor)):
        roots.extend(("project", "skill", project / folder)
                     for folder in (".agents/skills", ".codex/skills", ".claude/skills", "skills"))
        roots.extend(("project", "command", project / folder)
                     for folder in (".claude/commands", ".codex/commands"))
    for harness in (config_root("CODEX_HOME", home / ".codex"),
                    config_root("CLAUDE_CONFIG_DIR", home / ".claude"),
                    home / ".agents"):
        roots.append(("user", "skill", harness / "skills"))
        roots.append(("user", "command", harness / "commands"))
    roots.extend(("explicit", "any", absolute(path)) for path in extra)
    return list(dict.fromkeys(roots))


def context(args):
    home = Path.home().resolve()
    project = Path(args.project).expanduser().resolve(strict=True) if args.project else project_for(Path.cwd().resolve(), home)
    if not project.is_dir():
        raise ValueError("--project must be a directory")
    roots = root_specs(project, home, ())
    scope_key = [str(project), [(source, kind, str(path)) for source, kind, path in roots]]
    scope = hashlib.sha256(json.dumps(scope_key).encode()).hexdigest()
    cache = config_root("XDG_CACHE_HOME", home / ".cache")
    db = absolute(args.db) if args.db else cache / "hstack" / "catalog" / (scope[:24] + ".sqlite3")
    return project, scope, db


def approved_roots(roots):
    approved = set()
    for source, _, root in roots:
        if source not in ("explicit", "user"):
            continue
        try:
            target = root.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if source == "explicit" or root == target:
            approved.add(target)
    return approved


def permitted(target, project, approved):
    if any(under(target, boundary) for boundary in approved):
        return True
    if project in (Path.home(), Path(project.anchor)) or not under(target, project):
        return False
    return not any((path / ".git").exists() for path in target.parents if path != project and under(path, project))


def clean(text, length):
    return " ".join("".join(char if char.isprintable() or char.isspace() else " " for char in text).split())[:length]


def yaml_text(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
            if isinstance(value, str):
                return value
        except ValueError:
            pass
    return re.split(r"\s+#", raw, maxsplit=1)[0]


def yaml_values(raw, continuation):
    if re.fullmatch(r"[|>][1-9]?[+-]?|[|>][+-]?[1-9]?", raw):
        return [" ".join(line.strip() for line in continuation)]
    if raw.startswith("[") and raw.endswith("]"):
        items = re.findall(r'''(?:"(?:\\.|[^"\\])*"|'(?:''|[^'])*'|[^,])+''', raw[1:-1])
        return [yaml_text(item) for item in items if item.strip()]
    items = [line.strip()[2:] for line in continuation if line.strip().startswith("- ")]
    if not raw and items:
        return [yaml_text(item) for item in items]
    return [yaml_text(" ".join([raw, *[line.strip() for line in continuation]]).strip())]


def frontmatter(text):
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next((index for index, line in enumerate(lines[1:], 1) if line in ("---", "...")), None)
    if end is None:
        return {}
    pairs = []
    metadata = False
    for line in lines[1:end]:
        match = re.match(r"^( *)([a-z][a-z-]*):\s*(.*)$", line)
        if match:
            indent, key, raw = match.groups()
            if not indent:
                metadata = key == "metadata"
            if key in FIELDS and (not indent or metadata):
                pairs.append((key, raw, [], len(indent)))
                continue
        if pairs and (not line.strip() or len(line) - len(line.lstrip()) > pairs[-1][3]):
            pairs[-1][2].append(line)
    return {key: yaml_values(raw, continuation) for key, raw, continuation, _ in pairs}


def open_markdown(path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    stream = os.fdopen(fd, "rb")
    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
        stream.close()
        raise ValueError("Expected a regular Markdown file")
    return stream


def read_header(path):
    with open_markdown(path) as stream:
        first = stream.readline(MAX_HEADER)
        if first.decode("utf-8-sig", errors="replace").strip() != "---":
            return ""
        remaining = MAX_HEADER - len(first)
        lines = [first]
        while remaining > 0:
            line = stream.readline(remaining)
            if not line:
                break
            lines.append(line)
            remaining -= len(line)
            if line.rstrip(b"\r\n") in (b"---", b"..."):
                return b"".join(lines).decode("utf-8", errors="replace")
    return ""


def entry_for(path, target, kind, source, root):
    metadata = frontmatter(read_header(target))
    if kind == "skill":
        fallback = path.parent.name
    else:
        fallback = ":".join(path.relative_to(root).with_suffix("").parts)
    name = clean((metadata.get("name") or [""])[0], 120) or clean(fallback, 120)
    if not name:
        return None
    description = clean((metadata.get("description") or [""])[0], 800)
    triggers = clean(" ".join(metadata.get("trigger", []) + metadata.get("triggers", [])), 500)
    aliases = clean(" ".join(metadata.get("aliases", [])), 400)
    related = [clean(value, 120) for value in metadata.get("related", []) if value.strip()][:16]
    slug = re.sub(r"[^\w:-]+", "-", name.casefold()).strip("-:")[:72] or kind
    return (slug, kind, source, str(path), str(target), str(root), name, description, triggers, aliases, json.dumps(related))


def collect(project, roots):
    entries = {}
    paths_checked = 0
    truncated = False
    approved = approved_roots(roots)
    for source, kind, root in roots:
        if not root.exists():
            continue
        seen_dirs = set()
        stack = [(root, 0)]

        while stack:
            path, depth = stack.pop()
            paths_checked += 1
            if paths_checked > MAX_PATHS or len(entries) >= MAX_ENTRIES:
                return list(entries.values()), True
            try:
                target = path.resolve(strict=True)
                if not permitted(target, project, approved):
                    continue
                if target.is_dir():
                    if target in seen_dirs:
                        continue
                    if depth > MAX_DEPTH:
                        continue
                    seen_dirs.add(target)
                    if kind != "command":
                        skill_file = path / "SKILL.md"
                        if skill_file.is_file():
                            skill_target = skill_file.resolve(strict=True)
                            if permitted(skill_target, project, approved):
                                stack.append((skill_file, depth + 1))
                                continue
                    with os.scandir(path) as children:
                        sampled = list(islice(children, MAX_PATHS + 1))
                    if len(sampled) > MAX_PATHS:
                        truncated = True
                    paths = [path / child.name for child in sampled[:MAX_PATHS]
                             if not child.name.startswith(".") and child.name.casefold() not in EXCLUDED]
                    stack.extend((child, depth + 1) for child in sorted(paths, reverse=True))
                    continue
                if kind in ("skill", "any") and path.name == "SKILL.md":
                    entry_kind = "skill"
                elif kind in ("command", "any") and path.suffix.lower() == ".md":
                    if kind == "any" and "commands" not in (root.name, *path.relative_to(root).parts[:-1]):
                        continue
                    entry_kind = "command"
                else:
                    continue
                key = (entry_kind, target)
                if key not in entries and target.is_file():
                    entry = entry_for(path, target, entry_kind, source, root)
                    if entry:
                        entries[key] = entry
            except (OSError, RuntimeError, ValueError):
                continue

    return list(entries.values()), truncated


def registered_roots(connection, scope):
    return [row[0] for row in connection.execute("SELECT path FROM roots WHERE scope = ? ORDER BY path", (scope,))]


def sync(db, project, scope, additions, removals):
    db.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with closing(sqlite3.connect(db, timeout=20)) as connection:
        connection.executescript(SCHEMA)
        connection.execute("PRAGMA secure_delete = ON")
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            paths = set(registered_roots(connection, scope))
            paths.update(str(absolute(path)) for path in additions)
            paths.difference_update(str(absolute(path)) for path in removals)
            roots = root_specs(project, Path.home().resolve(), sorted(paths))
            entries, truncated = collect(project, roots)
            connection.execute("DELETE FROM roots WHERE scope = ?", (scope,))
            connection.executemany("INSERT INTO roots VALUES (?, ?)", ((scope, path) for path in sorted(paths)))
            connection.execute("DELETE FROM entries WHERE scope = ?", (scope,))
            duplicates = {}
            for slug, *_ in entries:
                duplicates[slug] = duplicates.get(slug, 0) + 1
            for slug, kind, source, path, *rest in entries:
                if duplicates[slug] > 1:
                    suffix = hashlib.sha256(path.encode()).hexdigest()[:10]
                    slug = f"{slug}@{suffix}"
                connection.execute(
                    "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (scope, slug, kind, source, path, *rest),
                )
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            connection.execute("INSERT OR REPLACE INTO scopes VALUES (?, ?, ?)", (scope, now, int(truncated)))
    return len(entries), truncated


def tokens(text):
    terms = set(re.findall(r"[^\W_]+", text.casefold())) - STOP
    return {term[:-1] if len(term) > 4 and term.endswith("s") and not term.endswith("ss") else term for term in terms}


def concepts(text):
    terms = tokens(text)
    return {index for index, group in enumerate(CONCEPTS) if any(tokens(phrase) <= terms for phrase in group)}


def score(row, query, query_terms, query_concepts, routed):
    name, aliases, triggers, description = (row[key] for key in ("name", "aliases", "triggers", "description"))
    heading = " ".join((name, aliases, triggers))
    name_terms = tokens(name)
    significant = query_terms - WEAK
    name_matches = len(significant & name_terms)
    heading_matches = len(significant & tokens(heading))
    description_matches = len(significant & tokens(description))
    concept_matches = len(query_concepts & concepts(heading + " " + description))
    title_concepts = len(query_concepts & concepts(name))
    normalized = query.casefold().strip("/").strip()
    exact = normalized in (name.casefold(), row["id"].casefold()) or bool(name_terms and name_terms == query_terms)
    if name.casefold() in ROUTERS and not (exact or len(CONCEPTS) - 1 in query_concepts):
        return 0
    phrase = len(significant) >= 2 and normalized in description.casefold()
    learned_match = row["path"] in routed
    named_match = len(name_terms) >= 2 and name_terms <= query_terms
    distinct_single = len(significant) == len(query_terms) == 1 and description_matches
    if not (exact or learned_match or named_match or heading_matches or description_matches >= 2
            or distinct_single or concept_matches):
        return 0
    relevance = (150 * exact + 125 * named_match + 90 * learned_match + 14 * name_matches + 6 * heading_matches
                 + 3 * description_matches + 8 * phrase + 4 * concept_matches + 22 * title_concepts)
    return relevance + {"project": 2, "explicit": 1, "user": 0}[row["source"]]


def path_label(path, project):
    value = Path(path)
    if under(value, project):
        return clean(str(value.relative_to(project)), 300)
    home = Path.home()
    if under(value, home):
        return clean("~/" + str(value.relative_to(home)), 300)
    return clean(path, 300)


def search_rows(rows, query, limit, project, routes):
    query_terms = tokens(query)
    query_concepts = concepts(query)
    routed = {path for phrase, path in routes if tokens(phrase) <= query_terms}
    matches = sorted(
        ((score(row, query, query_terms, query_concepts, routed), row) for row in rows),
        key=lambda item: (-item[0], item[1]["name"].casefold(), item[1]["id"]),
    )
    winners = [row for rank, row in matches if rank > 0][:limit]
    if not winners:
        print("No matching skills or commands.")
        return
    names = {}
    for row in rows:
        for label in (row["name"], row["id"]):
            names.setdefault(label.casefold(), []).append(row["id"])
    for row in winners:
        location = path_label(row["path"], project)
        print(f"{row['id']} [{row['source']} {row['kind']}] {location}")
        if row["description"]:
            print(f"  {row['description']}")
        if row["triggers"]:
            print(f"  Triggers: {row['triggers']}")
        related = sorted({item for label in json.loads(row["related"]) for item in names.get(label.casefold(), ())
                          if item != row["id"]})
        if related:
            print("  Related: " + ", ".join(related[:5]))


def show(row, project, roots):
    path = Path(row["path"])
    root = Path(row["root"])
    target = path.resolve(strict=True)
    valid_root = any(source == row["source"] and configured == root and kind in ("any", row["kind"])
                     for source, kind, configured in roots)
    if not valid_root or str(target) != row["target"] or not under(path, root):
        raise ValueError("Skill path changed. Run sync before opening it.")
    if not permitted(target, project, approved_roots(roots)):
        raise ValueError("Skill path is outside the active scope. Run sync before opening it.")
    with open_markdown(target) as stream:
        data = stream.read(MAX_BODY + 1)
    body = data[:MAX_BODY].decode("utf-8", errors="replace")
    # Preserve Markdown whitespace while removing terminal control characters.
    body = "".join(char for char in body if char.isprintable() or char in "\n\r\t")
    print(body, end="" if body.endswith("\n") else "\n")
    if len(data) > MAX_BODY:
        print(f"\n[Output limited to the first {MAX_BODY // 1024} KiB.]")


def shared_options(parser, defaults, root_dest):
    parser.add_argument("--project", metavar="DIR", default=None if defaults else argparse.SUPPRESS,
                        help="anchor discovery to this project directory")
    parser.add_argument("--root", metavar="DIR", action="append", dest=root_dest, default=argparse.SUPPRESS,
                        help="also index this directory (repeatable)")
    parser.add_argument("--db", metavar="FILE", default=None if defaults else argparse.SUPPRESS,
                        help="override the private cache path")


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    shared_options(parser, True, "root_main")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("sync", "refresh metadata for the active project and roots"),
        ("status", "show cache status for the active scope"),
        ("search", "rank cached metadata by name, workflow, trigger or description"),
        ("show", "read one indexed Markdown file by its exact ID"),
    ):
        sub = subparsers.add_parser(command, help=help_text)
        shared_options(sub, False, "root_sub")
        if command == "sync":
            sub.add_argument("--forget-root", action="append", default=[], metavar="DIR",
                             help="remove a previously registered root (repeatable)")
        if command == "search":
            sub.add_argument("query", nargs="+")
            sub.add_argument("--limit", type=int, choices=range(1, 21), default=3, metavar="1-20")
        if command == "show":
            sub.add_argument("id")
    alias = subparsers.add_parser("alias", help="manage learned routes for the active project")
    shared_options(alias, False, "root_sub")
    operations = alias.add_subparsers(dest="operation", required=True)
    for operation in ("add", "list", "remove"):
        action = operations.add_parser(operation)
        shared_options(action, False, "root_alias")
        if operation != "list":
            action.add_argument("phrase")
        if operation == "add":
            action.add_argument("id")
    args = parser.parse_args(argv)
    args.root = [root for position in ("root_main", "root_sub", "root_alias") for root in getattr(args, position, ())]
    return args


def change_alias(connection, scope, args):
    phrase = clean(args.phrase.casefold(), 160)
    if not tokens(phrase) or len(args.phrase) > 160:
        raise ValueError("Use a routing phrase of 1–160 characters with at least one searchable word.")
    with connection:
        if args.operation == "remove":
            deleted = connection.execute("DELETE FROM aliases WHERE scope = ? AND phrase = ?", (scope, phrase))
            if not deleted.rowcount:
                raise ValueError("No route found for that phrase in this scope.")
            print(f"Removed route: {phrase}")
            return
        row = connection.execute("SELECT path FROM entries WHERE scope = ? AND id = ?", (scope, args.id)).fetchone()
        if row is None:
            raise ValueError("ID not found in this scope. Run search first.")
        connection.execute("INSERT OR REPLACE INTO aliases VALUES (?, ?, ?)", (scope, phrase, row["path"]))
        print(f"Learned route: {phrase} -> {args.id}")


def main(argv=None):
    args = parse_args(argv)
    try:
        project, scope, db = context(args)
        if args.command == "sync":
            os.umask(0o077)
            count, truncated = sync(db, project, scope, args.root, args.forget_root)
            notice = " (scan limit reached)" if truncated else ""
            print(f"Indexed {count} skills and commands{notice}.")
            return 0
        if not db.is_file():
            raise ValueError("No catalog for this scope. Run sync.")
        mode = "rw" if args.command == "alias" and args.operation != "list" else "ro"
        with closing(sqlite3.connect(db.as_uri() + "?mode=" + mode, uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            info = connection.execute("SELECT * FROM scopes WHERE scope = ?", (scope,)).fetchone()
            if info is None:
                raise ValueError("No catalog for this scope. Run sync.")
            registered = registered_roots(connection, scope)
            unknown = {str(absolute(path)) for path in args.root} - set(registered)
            if unknown:
                raise ValueError("Register library roots using sync --root DIR.")
            roots = root_specs(project, Path.home().resolve(), registered)
            if args.command == "alias":
                if args.operation != "list":
                    change_alias(connection, scope, args)
                else:
                    routes = connection.execute(
                        """SELECT aliases.phrase, entries.id FROM aliases
                        LEFT JOIN entries ON aliases.scope = entries.scope AND aliases.path = entries.path
                        WHERE aliases.scope = ? ORDER BY aliases.phrase""", (scope,),
                    ).fetchall()
                    if not routes:
                        print("No learned routes in this scope.")
                    for phrase, skill_id in routes:
                        print(f"{phrase} -> {skill_id or '(missing skill)'}")
                return 0
            if args.command == "show":
                row = connection.execute("SELECT * FROM entries WHERE scope = ? AND id = ?", (scope, args.id)).fetchone()
                if row is None:
                    raise ValueError("ID not found in this scope. Run search first.")
                show(row, project, roots)
                return 0
            rows = connection.execute("SELECT * FROM entries WHERE scope = ?", (scope,)).fetchall()
            routes = connection.execute("SELECT phrase, path FROM aliases WHERE scope = ?", (scope,)).fetchall()
        if args.command == "status":
            print(f"{len(rows)} indexed in this scope. Last sync: {info['synced_at']}.")
            if info["truncated"]:
                print("The last sync reached a scan limit.")
            for path in registered:
                print(f"Registered root: {path_label(path, project)}")
        else:
            query = " ".join(args.query).strip()
            if not query or len(query) > 500:
                raise ValueError("Search query must contain 1–500 characters.")
            search_rows(rows, query, args.limit, project, routes)
        return 0
    except (OSError, RuntimeError, sqlite3.Error, ValueError) as error:
        print(f"catalog: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
