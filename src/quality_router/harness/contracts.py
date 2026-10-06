"""Breaking-change detection for JSON Schema, Avro and OpenAPI (JSON) contracts.

The research has no direct evidence for cross-repo agent coordination (P27);
the closest evidence says verify deterministically and never trust a version
bump (2605.24397, 2608.20167, 2606.24446). So contracts are the seam: every
change is classified mechanically, and consumers are checked against providers.

Roles (JSON Schema / OpenAPI):
  output - this repo produces the payload; consumers read it (delivery API,
           normalized content events). Removing or loosening breaks readers.
  input  - this repo accepts the payload (ingestion endpoints). Tightening or
           adding requirements breaks senders.
Avro modes: backward (new reader, old data), forward (old reader, new data), full.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quality_router.harness.report import GateResult, Level

Json = Any


@dataclass(frozen=True)
class Change:
    level: Level
    code: str
    pointer: str
    message: str


class ContractError(ValueError):
    pass


def read_contract(spec: str, cwd: Path) -> Json:
    """Load `path` or `git:REF:path` as JSON."""
    if spec.startswith("git:"):
        _, ref, rel = spec.split(":", 2)
        proc = subprocess.run(["git", "-C", str(cwd), "show", f"{ref}:{rel}"],
                              capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise ContractError(proc.stderr.strip() or f"cannot read {spec}")
        text, name = proc.stdout, rel
    else:
        path = Path(spec) if Path(spec).is_absolute() else cwd / spec
        if not path.is_file():
            raise ContractError(f"contract not found: {spec}")
        text, name = path.read_text(encoding="utf-8"), path.name
    if name.endswith((".yaml", ".yml")):
        raise ContractError(f"{spec}: YAML is not supported (stdlib only); export JSON "
                            "(e.g. springdoc /v3/api-docs) and diff that")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"{spec}: invalid JSON ({exc})") from exc


def detect_kind(doc: Json) -> str:
    if isinstance(doc, dict) and "openapi" in doc:
        return "openapi"
    if isinstance(doc, dict) and doc.get("type") in ("record", "enum", "fixed"):
        return "avro"
    if isinstance(doc, list):
        return "avro"
    return "jsonschema"


def diff_contracts(old: Json, new: Json, role: str = "output", avro_mode: str = "full",
                   kind: str | None = None) -> tuple[str, list[Change]]:
    kind = kind or detect_kind(new)
    if kind != detect_kind(old):
        raise ContractError(f"contract kinds differ: {detect_kind(old)} -> {kind}")
    if kind == "openapi":
        return kind, _OpenApiDiff(old, new).run()
    if kind == "avro":
        return kind, _AvroDiff(avro_mode).run(old, new)
    return kind, _SchemaDiff(old, new, role).run()


# --------------------------------------------------------------------------- #
# JSON Schema
# --------------------------------------------------------------------------- #

_TIGHTEN_UP = ("minLength", "minItems", "minimum", "exclusiveMinimum", "minProperties")
_TIGHTEN_DOWN = ("maxLength", "maxItems", "maximum", "exclusiveMaximum", "maxProperties")


def _resolve(node: Json, root: Json, seen: frozenset[str] = frozenset()) -> Json:
    while isinstance(node, dict) and isinstance(node.get("$ref"), str):
        ref = node["$ref"]
        if not ref.startswith("#/") or ref in seen:
            return node
        seen = seen | {ref}
        target: Json = root
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or part not in target:
                return node
            target = target[part]
        node = target
    return node


def _types(node: Json) -> set[str] | None:
    if not isinstance(node, dict):
        return None
    declared = node.get("type")
    if isinstance(declared, str):
        types = {declared}
    elif isinstance(declared, list):
        types = {str(t) for t in declared}
    elif "properties" in node:
        types = {"object"}
    elif "items" in node:
        types = {"array"}
    else:
        return None
    if node.get("nullable") is True:
        types.add("null")
    return types


class _SchemaDiff:
    def __init__(self, old_root: Json, new_root: Json, role: str) -> None:
        if role not in ("output", "input"):
            raise ContractError(f"role must be output or input, not {role!r}")
        self.old_root = old_root
        self.new_root = new_root
        self.role = role
        self.changes: list[Change] = []
        self._visited: set[tuple[int, int]] = set()

    def run(self) -> list[Change]:
        self.compare(self.old_root, self.new_root, "#")
        return self.changes

    def _add(self, level: Level, code: str, pointer: str, message: str) -> None:
        self.changes.append(Change(level, code, pointer, message))

    def compare(self, old: Json, new: Json, ptr: str) -> None:
        old = _resolve(old, self.old_root)
        new = _resolve(new, self.new_root)
        if not isinstance(old, dict) or not isinstance(new, dict):
            return
        key = (id(old), id(new))
        if key in self._visited:
            return
        self._visited.add(key)
        reader = self.role == "output"
        self._compare_types(old, new, ptr, reader)
        self._compare_enum(old, new, ptr, reader)
        self._compare_bounds(old, new, ptr, reader)
        if old.get("pattern") != new.get("pattern") and ("pattern" in old or "pattern" in new):
            self._add("warning", "pattern_changed", ptr,
                      f"pattern {old.get('pattern')!r} -> {new.get('pattern')!r}")
        self._compare_object(old, new, ptr, reader)
        if "items" in old and "items" in new:
            self.compare(old["items"], new["items"], f"{ptr}/items")
        for combo in ("allOf", "anyOf", "oneOf"):
            olds, news = old.get(combo), new.get(combo)
            if isinstance(olds, list) and isinstance(news, list):
                for i, (o, n) in enumerate(zip(olds, news, strict=False)):
                    self.compare(o, n, f"{ptr}/{combo}/{i}")
                if len(olds) != len(news):
                    self._add("warning", f"{combo}_changed", ptr,
                              f"{combo} branches {len(olds)} -> {len(news)}")

    def _compare_types(self, old: dict, new: dict, ptr: str, reader: bool) -> None:
        old_t, new_t = _types(old), _types(new)
        if old_t is None or new_t is None or old_t == new_t:
            return
        added, removed = new_t - old_t, old_t - new_t
        if "integer" in removed and "number" in added and not reader:
            removed = removed - {"integer"}
        if reader and added:
            self._add("error", "type_widened", ptr,
                      f"producer may now emit {sorted(added)}; readers expect {sorted(old_t)}")
        if not reader and removed:
            self._add("error", "type_narrowed", ptr,
                      f"{sorted(removed)} no longer accepted; senders still send it")
        if (reader and removed and not added) or (not reader and added and not removed):
            self._add("info", "type_compatible", ptr, f"type {sorted(old_t)} -> {sorted(new_t)}")

    def _compare_enum(self, old: dict, new: dict, ptr: str, reader: bool) -> None:
        if "enum" not in old or "enum" not in new:
            if "enum" in new and "enum" not in old and not reader:
                self._add("error", "enum_introduced", ptr, "value now restricted to an enum")
            return
        old_v = [json.dumps(v, sort_keys=True) for v in old["enum"]]
        new_v = [json.dumps(v, sort_keys=True) for v in new["enum"]]
        added = [v for v in new_v if v not in old_v]
        removed = [v for v in old_v if v not in new_v]
        if added and reader:
            self._add("warning", "enum_value_added", ptr,
                      f"new values {added}; exhaustive consumers (switch/when) must handle them")
        if removed and not reader:
            self._add("error", "enum_value_removed", ptr, f"values {removed} no longer accepted")
        if removed and reader:
            self._add("info", "enum_value_removed", ptr, f"values {removed} no longer emitted")

    def _compare_bounds(self, old: dict, new: dict, ptr: str, reader: bool) -> None:
        for key in _TIGHTEN_UP + _TIGHTEN_DOWN:
            if key not in old and key not in new:
                continue
            o, n = old.get(key), new.get(key)
            if o == n or isinstance(o, bool) or isinstance(n, bool):
                continue
            if key in _TIGHTEN_UP:
                tightened = n is not None and (o is None or n > o)
            else:
                tightened = n is not None and (o is None or n < o)
            if tightened and not reader:
                self._add("error", "constraint_tightened", f"{ptr}/{key}", f"{key} {o} -> {n}")
            elif not tightened and reader:
                self._add("warning", "constraint_loosened", f"{ptr}/{key}",
                          f"{key} {o} -> {n}; readers may receive values they reject")

    def _compare_object(self, old: dict, new: dict, ptr: str, reader: bool) -> None:
        old_props = old.get("properties") if isinstance(old.get("properties"), dict) else {}
        new_props = new.get("properties") if isinstance(new.get("properties"), dict) else {}
        old_req = set(old.get("required") or [])
        new_req = set(new.get("required") or [])
        closed_old = old.get("additionalProperties") is False
        closed_new = new.get("additionalProperties") is False
        for name in sorted(set(old_props) | set(new_props)):
            child = f"{ptr}/properties/{name}"
            if name in old_props and name not in new_props:
                if reader:
                    self._add("error", "property_removed", child,
                              f"`{name}` removed; consumers reading it break")
                elif closed_new:
                    self._add("error", "property_rejected", child,
                              f"`{name}` removed and additionalProperties=false; senders break")
                else:
                    self._add("warning", "property_ignored", child,
                              f"`{name}` removed; senders' value is now ignored")
            elif name in new_props and name not in old_props:
                if reader and closed_old:
                    self._add("error", "property_added_closed", child,
                              f"`{name}` added but old schema had additionalProperties=false")
                elif not reader and name in new_req:
                    self._add("error", "required_property_added", child,
                              f"new required `{name}`; existing senders omit it")
                else:
                    self._add("info", "property_added", child, f"`{name}` added")
            else:
                self.compare(old_props[name], new_props[name], child)
        for name in sorted(old_req - new_req):
            if reader and name in new_props:
                self._add("error", "property_now_optional", f"{ptr}/properties/{name}",
                          f"`{name}` no longer required; consumers may get it absent")
        for name in sorted(new_req - old_req):
            if not reader and name in old_props:
                self._add("error", "property_now_required", f"{ptr}/properties/{name}",
                          f"`{name}` now required; existing senders may omit it")
        if not reader and closed_new and not closed_old:
            self._add("error", "additional_properties_closed", ptr,
                      "additionalProperties now false; senders with extra fields break")


# --------------------------------------------------------------------------- #
# OpenAPI 3 (JSON)
# --------------------------------------------------------------------------- #

_METHODS = ("get", "put", "post", "delete", "patch", "head", "options", "trace")


class _OpenApiDiff:
    def __init__(self, old: Json, new: Json) -> None:
        self.old = old
        self.new = new
        self.changes: list[Change] = []

    def run(self) -> list[Change]:
        old_paths = self.old.get("paths") or {}
        new_paths = self.new.get("paths") or {}
        for path in sorted(old_paths):
            for method in _METHODS:
                old_op = (old_paths.get(path) or {}).get(method)
                if old_op is None:
                    continue
                ptr = f"#/paths/{path}/{method}"
                new_op = (new_paths.get(path) or {}).get(method)
                if new_op is None:
                    self.changes.append(Change("error", "operation_removed", ptr,
                                               f"{method.upper()} {path} removed"))
                    continue
                self._parameters(old_paths[path], new_paths[path], old_op, new_op, ptr)
                self._request(old_op, new_op, ptr)
                self._responses(old_op, new_op, ptr)
        for path in sorted(set(new_paths) - set(old_paths)):
            self.changes.append(Change("info", "path_added", f"#/paths/{path}", f"{path} added"))
        return self.changes

    def _schema_diff(self, old: Json, new: Json, role: str, ptr: str) -> None:
        differ = _SchemaDiff(self.old, self.new, role)
        differ.compare(old, new, ptr)
        self.changes.extend(differ.changes)

    def _parameters(self, old_item: dict, new_item: dict, old_op: dict, new_op: dict,
                    ptr: str) -> None:
        def index(item: dict, op: dict, root: Json) -> dict[tuple[str, str], dict]:
            params = list(item.get("parameters") or []) + list(op.get("parameters") or [])
            out: dict[tuple[str, str], dict] = {}
            for raw in params:
                param = _resolve(raw, root)
                if isinstance(param, dict) and "name" in param:
                    out[(param.get("in", ""), param["name"])] = param
            return out

        old_params = index(old_item, old_op, self.old)
        new_params = index(new_item, new_op, self.new)
        for key, param in sorted(new_params.items()):
            was = old_params.get(key)
            required = bool(param.get("required")) or key[0] == "path"
            if required and (was is None or not (was.get("required") or key[0] == "path")):
                self.changes.append(Change("error", "required_parameter_added",
                                           f"{ptr}/parameters/{key[0]}:{key[1]}",
                                           f"{key[0]} parameter `{key[1]}` now required"))
            if was is not None and "schema" in was and "schema" in param:
                self._schema_diff(was["schema"], param["schema"], "input",
                                  f"{ptr}/parameters/{key[0]}:{key[1]}")
        for key in sorted(set(old_params) - set(new_params)):
            self.changes.append(Change("warning", "parameter_removed",
                                       f"{ptr}/parameters/{key[0]}:{key[1]}",
                                       f"{key[0]} parameter `{key[1]}` removed (now ignored)"))

    def _request(self, old_op: dict, new_op: dict, ptr: str) -> None:
        old_body = _resolve(old_op.get("requestBody"), self.old)
        new_body = _resolve(new_op.get("requestBody"), self.new)
        if not isinstance(new_body, dict):
            return
        if not isinstance(old_body, dict):
            if new_body.get("required"):
                self.changes.append(Change("error", "request_body_required", f"{ptr}/requestBody",
                                           "request body added and required"))
            return
        if new_body.get("required") and not old_body.get("required"):
            self.changes.append(Change("error", "request_body_required", f"{ptr}/requestBody",
                                       "request body now required"))
        old_content = old_body.get("content") or {}
        new_content = new_body.get("content") or {}
        for media in sorted(old_content):
            cptr = f"{ptr}/requestBody/{media}"
            if media not in new_content:
                self.changes.append(Change("error", "media_type_removed", cptr,
                                           f"request media type {media} no longer accepted"))
                continue
            self._schema_diff((old_content[media] or {}).get("schema"),
                              (new_content[media] or {}).get("schema"), "input", cptr)

    def _responses(self, old_op: dict, new_op: dict, ptr: str) -> None:
        old_resp = old_op.get("responses") or {}
        new_resp = new_op.get("responses") or {}
        for status in sorted(old_resp):
            if not str(status).startswith("2"):
                continue
            rptr = f"{ptr}/responses/{status}"
            if status not in new_resp:
                self.changes.append(Change("error", "response_removed", rptr,
                                           f"success response {status} removed"))
                continue
            old_r = _resolve(old_resp[status], self.old) or {}
            new_r = _resolve(new_resp[status], self.new) or {}
            old_content = old_r.get("content") or {}
            new_content = new_r.get("content") or {}
            for media in sorted(old_content):
                if media not in new_content:
                    self.changes.append(Change("error", "media_type_removed", f"{rptr}/{media}",
                                               f"response media type {media} no longer produced"))
                    continue
                self._schema_diff((old_content[media] or {}).get("schema"),
                                  (new_content[media] or {}).get("schema"), "output",
                                  f"{rptr}/{media}")


# --------------------------------------------------------------------------- #
# Avro
# --------------------------------------------------------------------------- #

_PROMOTIONS = {
    "int": {"long", "float", "double"},
    "long": {"float", "double"},
    "float": {"double"},
    "string": {"bytes"},
    "bytes": {"string"},
}


class _AvroDiff:
    def __init__(self, mode: str) -> None:
        if mode not in ("backward", "forward", "full"):
            raise ContractError(f"avro mode must be backward, forward or full, not {mode!r}")
        self.mode = mode
        self.changes: list[Change] = []
        self.old_named: dict[str, Json] = {}
        self.new_named: dict[str, Json] = {}

    def run(self, old: Json, new: Json) -> list[Change]:
        self._register(old, self.old_named)
        self._register(new, self.new_named)
        if self.mode in ("backward", "full"):
            self._readable(writer=old, reader=new, ptr="#", direction="backward")
        if self.mode in ("forward", "full"):
            self._readable(writer=new, reader=old, ptr="#", direction="forward")
        return self.changes

    def _register(self, node: Json, table: dict[str, Json]) -> None:
        if isinstance(node, list):
            for branch in node:
                self._register(branch, table)
        elif isinstance(node, dict):
            if node.get("type") in ("record", "enum", "fixed") and "name" in node:
                table[node["name"]] = node
                if "namespace" in node:
                    table[f"{node['namespace']}.{node['name']}"] = node
            for field_ in node.get("fields") or []:
                self._register(field_.get("type"), table)
            for key in ("items", "values"):
                if key in node:
                    self._register(node[key], table)

    def _deref(self, node: Json, table: dict[str, Json]) -> Json:
        if isinstance(node, str) and node in table:
            return table[node]
        if isinstance(node, dict) and node.get("type") in ("array", "map", "record", "enum",
                                                            "fixed"):
            return node
        if isinstance(node, dict) and isinstance(node.get("type"), str | list):
            return self._deref(node["type"], table)
        return node

    @staticmethod
    def _name(node: Json) -> str:
        if isinstance(node, str):
            return node
        if isinstance(node, list):
            return "union"
        if isinstance(node, dict):
            kind = node.get("type")
            return node.get("name", kind) if kind in ("record", "enum", "fixed") else str(kind)
        return "unknown"

    def _readable(self, writer: Json, reader: Json, ptr: str, direction: str) -> None:
        w_table = self.old_named if direction == "backward" else self.new_named
        r_table = self.new_named if direction == "backward" else self.old_named
        writer = self._deref(writer, w_table)
        reader = self._deref(reader, r_table)
        if isinstance(writer, list) or isinstance(reader, list):
            w_branches = writer if isinstance(writer, list) else [writer]
            r_branches = reader if isinstance(reader, list) else [reader]
            for branch in w_branches:
                if not any(self._compatible(branch, r, w_table, r_table) for r in r_branches):
                    self._add(direction, "union_branch_unreadable", ptr,
                              f"writer branch {self._name(branch)} has no reader branch")
            return
        if not self._compatible(writer, reader, w_table, r_table):
            self._add(direction, "type_changed", ptr,
                      f"{self._name(writer)} -> {self._name(reader)} is not a valid promotion")
            return
        if isinstance(writer, dict) and writer.get("type") == "record":
            self._record(writer, reader, ptr, direction)
        elif isinstance(writer, dict) and writer.get("type") == "enum":
            missing = [s for s in writer.get("symbols", []) if s not in reader.get("symbols", [])]
            if missing and "default" not in reader:
                self._add(direction, "enum_symbol_unreadable", ptr,
                          f"symbols {missing} unknown to reader and no enum default")
        elif isinstance(writer, dict) and writer.get("type") in ("array", "map"):
            key = "items" if writer["type"] == "array" else "values"
            self._readable(writer.get(key), reader.get(key), f"{ptr}/{key}", direction)

    def _compatible(self, writer: Json, reader: Json, w_table: dict, r_table: dict) -> bool:
        writer = self._deref(writer, w_table)
        reader = self._deref(reader, r_table)
        w, r = self._name(writer), self._name(reader)
        if isinstance(reader, list):
            return any(self._compatible(writer, b, w_table, r_table) for b in reader)
        if w == r:
            return True
        return r in _PROMOTIONS.get(w, set())

    def _record(self, writer: dict, reader: dict, ptr: str, direction: str) -> None:
        w_fields = {f["name"]: f for f in writer.get("fields", [])}
        for field_ in reader.get("fields", []):
            names = [field_["name"], *field_.get("aliases", [])]
            match = next((w_fields[n] for n in names if n in w_fields), None)
            fptr = f"{ptr}/{field_['name']}"
            if match is None:
                if "default" not in field_:
                    self._add(direction, "field_without_default", fptr,
                              f"reader field `{field_['name']}` missing from writer and has no "
                              "default")
                continue
            self._readable(match.get("type"), field_.get("type"), fptr, direction)

    def _add(self, direction: str, code: str, ptr: str, message: str) -> None:
        self.changes.append(Change("error", f"{direction}_{code}", ptr, message))


# --------------------------------------------------------------------------- #
# Gate wrappers
# --------------------------------------------------------------------------- #

def run_contract_diff(old_spec: str, new_spec: str, cwd: Path, role: str, avro_mode: str,
                      strict: bool = False) -> GateResult:
    result = GateResult(gate="contracts-diff", strict=strict)
    kind, changes = diff_contracts(read_contract(old_spec, cwd), read_contract(new_spec, cwd),
                                   role=role, avro_mode=avro_mode)
    for change in changes:
        result.add(change.level, change.code, f"{change.pointer} {change.message}", new_spec)
    result.summary.update({"kind": kind, "role": role if kind != "avro" else avro_mode,
                           "breaking": sum(1 for c in changes if c.level == "error")})
    return result


def run_contract_check(manifest_path: Path, checkouts: Path | None,
                       strict: bool = False) -> GateResult:
    """Check every consumer's vendored contract against its provider. Reads only."""
    result = GateResult(gate="contracts-check", strict=strict)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = checkouts or manifest_path.parent
    repos: dict[str, Path] = {}
    for name, rel in (manifest.get("repos") or {}).items():
        repos[name] = (base / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
    edges: dict[str, set[str]] = {name: set() for name in repos}
    for contract in manifest.get("contracts") or []:
        name = contract.get("name", "?")
        provider = contract.get("provider") or {}
        p_repo = provider.get("repo", "")
        if p_repo not in repos or not repos[p_repo].is_dir():
            result.add("error", "repo_not_checked_out", f"provider repo `{p_repo}` missing",
                       name)
            continue
        p_file = repos[p_repo] / provider.get("path", "")
        if not p_file.is_file():
            result.add("error", "provider_contract_missing", str(p_file), name)
            continue
        new_doc = read_contract(str(p_file), base)
        for consumer in contract.get("consumers") or []:
            c_repo = consumer.get("repo", "")
            label = f"{name} -> {c_repo}"
            if c_repo not in repos or not repos[c_repo].is_dir():
                result.add("error", "repo_not_checked_out", f"consumer repo `{c_repo}` missing",
                           label)
                continue
            edges.setdefault(p_repo, set()).add(c_repo)
            c_file = repos[c_repo] / consumer.get("path", "")
            if not c_file.is_file():
                result.add("error", "consumer_contract_missing",
                           f"no vendored copy at {consumer.get('path', '')}", label)
                continue
            old_doc = read_contract(str(c_file), base)
            if old_doc == new_doc:
                continue
            _, changes = diff_contracts(old_doc, new_doc, role=contract.get("role", "output"),
                                        avro_mode=contract.get("avro_mode", "full"))
            breaking = [c for c in changes if c.level == "error"]
            if breaking:
                for change in breaking:
                    result.add("error", "consumer_breaking_drift",
                               f"{change.code} {change.pointer}: {change.message}", label)
            else:
                result.add("warning", "consumer_stale_copy",
                           f"vendored copy differs from provider ({len(changes)} non-breaking "
                           "changes); refresh it", label)
    order, cyclic = _merge_order(edges)
    if cyclic:
        result.add("warning", "contract_cycle",
                   f"provider/consumer cycle among {sorted(cyclic)}; no safe merge order")
    result.summary.update({"repos": len(repos), "merge_order": order})
    return result


def _merge_order(edges: dict[str, set[str]]) -> tuple[list[str], set[str]]:
    indegree = {node: 0 for node in edges}
    for targets in edges.values():
        for target in targets:
            indegree[target] = indegree.get(target, 0) + 1
    ready = sorted(n for n, d in indegree.items() if d == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for target in sorted(edges.get(node, ())):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
        ready.sort()
    return order, {n for n, d in indegree.items() if d > 0}
