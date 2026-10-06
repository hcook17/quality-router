"""qr contracts diff / check: JSON Schema, OpenAPI and Avro breaking-change rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.helpers import git
from quality_router.harness.contracts import (
    ContractError,
    _AvroDiff,
    _merge_order,
    _SchemaDiff,
    detect_kind,
    diff_contracts,
    read_contract,
    run_contract_check,
    run_contract_diff,
)


def codes(changes) -> list[str]:
    return sorted(c.code for c in changes)


def schema(**props) -> dict:
    return {"type": "object", "properties": props}


class TestReadContract:
    def test_path_git_yaml_and_invalid(self, repo: Path) -> None:
        (repo / "c.json").write_text('{"type": "string"}', encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "c")
        assert read_contract("c.json", repo) == {"type": "string"}
        assert read_contract(str(repo / "c.json"), Path("/")) == {"type": "string"}
        assert read_contract("git:HEAD:c.json", repo) == {"type": "string"}
        with pytest.raises(ContractError):
            read_contract("git:HEAD:missing.json", repo)
        with pytest.raises(ContractError):
            read_contract("missing.json", repo)
        (repo / "o.yaml").write_text("openapi: 3.0.0", encoding="utf-8")
        with pytest.raises(ContractError, match="YAML"):
            read_contract("o.yaml", repo)
        (repo / "bad.json").write_text("{", encoding="utf-8")
        with pytest.raises(ContractError, match="invalid JSON"):
            read_contract("bad.json", repo)

    def test_detect_kind(self) -> None:
        assert detect_kind({"openapi": "3.1.0"}) == "openapi"
        assert detect_kind({"type": "record"}) == "avro"
        assert detect_kind(["null", "string"]) == "avro"
        assert detect_kind({"type": "object"}) == "jsonschema"
        with pytest.raises(ContractError, match="kinds differ"):
            diff_contracts({"type": "object"}, {"openapi": "3"})


class TestJsonSchemaOutput:
    """Role output: we produce, consumers read."""

    def run(self, old, new) -> list[str]:
        return codes(diff_contracts(old, new, role="output")[1])

    def test_property_removed_and_now_optional(self) -> None:
        old = {**schema(id={"type": "string"}, title={"type": "string"}), "required": ["id"]}
        new = schema(title={"type": "string"}, extra={"type": "string"})
        assert self.run(old, new) == ["property_added", "property_removed"]
        old2 = {**schema(id={"type": "string"}), "required": ["id"]}
        assert self.run(old2, schema(id={"type": "string"})) == ["property_now_optional"]

    def test_closed_object_rejects_new_property(self) -> None:
        old = {**schema(id={"type": "string"}), "additionalProperties": False}
        new = schema(id={"type": "string"}, x={"type": "integer"})
        assert self.run(old, new) == ["property_added_closed"]

    def test_types_enums_bounds_pattern(self) -> None:
        assert self.run({"type": "string"}, {"type": ["string", "null"]}) == ["type_widened"]
        assert self.run({"type": ["string", "null"]}, {"type": "string"}) == ["type_compatible"]
        assert self.run({"type": "string"}, {"type": "string", "nullable": True}) == [
            "type_widened"]
        assert self.run({"enum": ["a"]}, {"enum": ["a", "b"]}) == ["enum_value_added"]
        assert self.run({"enum": ["a", "b"]}, {"enum": ["a"]}) == ["enum_value_removed"]
        assert self.run({"maxLength": 5}, {"maxLength": 10}) == ["constraint_loosened"]
        assert self.run({"maxLength": 10}, {"maxLength": 5}) == []
        assert self.run({"pattern": "a"}, {"pattern": "b"}) == ["pattern_changed"]
        assert self.run({"minimum": True}, {"minimum": 3}) == []

    def test_refs_items_and_combinators(self) -> None:
        old = {"$defs": {"Tag": {"type": "string"}},
               "type": "array", "items": {"$ref": "#/$defs/Tag"},
               "anyOf": [{"type": "string"}], "allOf": [{"$ref": "#/$defs/Tag"}]}
        new = {"$defs": {"Tag": {"type": "integer"}},
               "type": "array", "items": {"$ref": "#/$defs/Tag"},
               "anyOf": [{"type": "string"}, {"type": "null"}],
               "allOf": [{"$ref": "#/$defs/Tag"}]}
        assert self.run(old, new) == ["anyOf_changed", "type_widened"]

    def test_ref_edge_cases(self) -> None:
        cyclic = {"$defs": {"A": {"$ref": "#/$defs/A"}}, "properties": {"a": {"$ref": "#/$defs/A"}}}
        assert self.run(cyclic, cyclic) == []
        external = schema(a={"$ref": "other.json#/x"})
        assert self.run(external, external) == []
        dangling = schema(a={"$ref": "#/$defs/Nope"})
        assert self.run(dangling, dangling) == []
        escaped = {"$defs": {"a/b": {"type": "string"}},
                   "properties": {"x": {"$ref": "#/$defs/a~1b"}}}
        assert self.run(escaped, escaped) == []
        shared = {"$defs": {"T": {"type": "string"}},
                  "properties": {"a": {"$ref": "#/$defs/T"}, "b": {"$ref": "#/$defs/T"}}}
        assert self.run(shared, shared) == []
        assert self.run({"items": True}, {"items": {"type": "string"}}) == []


class TestJsonSchemaInput:
    """Role input: we accept, senders write."""

    def run(self, old, new) -> list[str]:
        return codes(diff_contracts(old, new, role="input")[1])

    def test_tightening_breaks_senders(self) -> None:
        assert self.run({"type": "string"}, {"type": "string", "enum": ["a"]}) == [
            "enum_introduced"]
        assert self.run({"enum": ["a", "b"]}, {"enum": ["a"]}) == ["enum_value_removed"]
        assert self.run({"minLength": 1}, {"minLength": 3}) == ["constraint_tightened"]
        assert self.run({}, {"maxItems": 3}) == ["constraint_tightened"]
        assert self.run({"type": ["string", "null"]}, {"type": "string"}) == ["type_narrowed"]
        assert self.run({"type": "integer"}, {"type": "number"}) == ["type_compatible"]
        assert self.run({"type": "string"}, {"type": ["string", "null"]}) == ["type_compatible"]

    def test_required_and_closed(self) -> None:
        old = schema(a={"type": "string"}, b={"type": "string"})
        new = {**schema(a={"type": "string"}, c={"type": "string"}), "required": ["a", "c"],
               "additionalProperties": False}
        assert self.run(old, new) == ["additional_properties_closed", "property_now_required",
                                      "property_rejected", "required_property_added"]
        assert self.run(old, schema(a={"type": "string"})) == ["property_ignored"]

    def test_bad_role(self) -> None:
        with pytest.raises(ContractError):
            _SchemaDiff({}, {}, "both")


def openapi(paths: dict, components: dict | None = None) -> dict:
    return {"openapi": "3.0.3", "paths": paths, "components": components or {}}


def ok(schema_: dict) -> dict:
    return {"200": {"content": {"application/json": {"schema": schema_}}}}


class TestOpenApi:
    def run(self, old, new) -> list[str]:
        return codes(diff_contracts(old, new)[1])

    def test_operations_paths_and_responses(self) -> None:
        old = openapi({"/items": {"get": {"responses": ok(schema(id={"type": "string"}))},
                                  "delete": {"responses": {}}},
                       "/x": {"get": {"responses": {"200": {}, "404": {}}}}})
        new = openapi({"/items": {"get": {"responses": ok(schema())}},
                       "/x": {"get": {"responses": {"201": {}}}},
                       "/new": {}})
        assert self.run(old, new) == ["operation_removed", "path_added", "property_removed",
                                      "response_removed"]

    def test_media_types(self) -> None:
        old = openapi({"/i": {"post": {
            "requestBody": {"content": {"application/xml": {}, "application/json": {}}},
            "responses": {"200": {"content": {"text/csv": {}}}}}}})
        new = openapi({"/i": {"post": {
            "requestBody": {"content": {"application/json": None}},
            "responses": {"200": {"content": {}}}}}})
        assert self.run(old, new) == ["media_type_removed", "media_type_removed"]

    def test_parameters_and_request_bodies(self) -> None:
        params = {"components": {"parameters": {"Q": {"name": "q", "in": "query",
                                                      "schema": {"type": "string"}}}}}
        old = {**openapi({"/i/{id}": {
            "parameters": [{"name": "id", "in": "path"}],
            "get": {"parameters": [{"$ref": "#/components/parameters/Q"},
                                   {"name": "gone", "in": "header"}, "junk"],
                    "responses": {}},
            "put": {"requestBody": {"content": {"application/json": {
                "schema": schema(a={"type": "string"})}}}, "responses": {}},
            "post": {"responses": {}},
            "patch": {"responses": {}}}}), **params}
        new = openapi({"/i/{id}": {
            "parameters": [{"name": "id", "in": "path"}],
            "get": {"parameters": [{"name": "q", "in": "query", "required": True,
                                    "schema": {"type": "string", "minLength": 2}},
                                   {"name": "page", "in": "query", "required": True}],
                    "responses": {}},
            "put": {"requestBody": {"required": True, "content": {"application/json": {
                "schema": {**schema(a={"type": "string"}), "required": ["a"]}}}},
                "responses": {}},
            "post": {"requestBody": {"required": True}, "responses": {}},
            "patch": {"requestBody": {"content": {}}, "responses": {}}}})
        assert self.run(old, new) == [
            "constraint_tightened", "parameter_removed", "property_now_required",
            "request_body_required", "request_body_required", "required_parameter_added",
            "required_parameter_added"]


def record(name: str, *fields: dict, **extra) -> dict:
    return {"type": "record", "name": name, "fields": list(fields), **extra}


class TestAvro:
    def run(self, old, new, mode: str = "full") -> list[str]:
        return codes(diff_contracts(old, new, avro_mode=mode)[1])

    def test_added_field_needs_default(self) -> None:
        old = record("Item", {"name": "id", "type": "string"})
        new = record("Item", {"name": "id", "type": "string"}, {"name": "lic", "type": "string"})
        assert self.run(old, new, "backward") == ["backward_field_without_default"]
        assert self.run(old, new, "forward") == []
        new_ok = record("Item", {"name": "id", "type": "string"},
                        {"name": "lic", "type": ["null", "string"], "default": None})
        assert self.run(old, new_ok) == []

    def test_promotions_unions_and_aliases(self) -> None:
        old = record("I", {"name": "n", "type": "int"}, {"name": "u", "type": ["null", "string"]})
        new = record("I", {"name": "n", "type": "long"},
                     {"name": "u", "type": "string"})
        assert self.run(old, new, "backward") == ["backward_union_branch_unreadable"]
        assert self.run(old, new, "forward") == ["forward_type_changed"]
        renamed = record("I", {"name": "count", "aliases": ["n"], "type": "int"},
                         {"name": "u", "type": ["null", "string"]})
        assert self.run(old, renamed, "backward") == []

    def test_enums_arrays_maps_and_named_refs(self) -> None:
        status = {"type": "enum", "name": "Status", "symbols": ["A", "B"]}
        old = {"type": "record", "name": "R", "namespace": "acme", "fields": [
            {"name": "s", "type": status},
            {"name": "again", "type": "acme.Status"},
            {"name": "tags", "type": {"type": "array", "items": "string"}},
            {"name": "attrs", "type": {"type": "map", "values": "int"}},
            {"name": "t", "type": {"type": "string", "logicalType": "uuid"}}]}
        new_status = {"type": "enum", "name": "Status", "symbols": ["A"]}
        new = {"type": "record", "name": "R", "namespace": "acme", "fields": [
            {"name": "s", "type": new_status},
            {"name": "again", "type": "acme.Status"},
            {"name": "tags", "type": {"type": "array", "items": "int"}},
            {"name": "attrs", "type": {"type": "map", "values": "long"}},
            {"name": "t", "type": "string"}]}
        assert self.run(old, new, "backward") == [
            "backward_enum_symbol_unreadable", "backward_enum_symbol_unreadable",
            "backward_type_changed"]
        defaulted = {**new_status, "default": "A"}
        new["fields"][0]["type"] = defaulted
        assert self.run(old, new, "backward") == ["backward_type_changed"]

    def test_mode_validation_and_names(self) -> None:
        with pytest.raises(ContractError):
            _AvroDiff("sideways")
        assert _AvroDiff._name(3) == "unknown"
        assert _AvroDiff._name(["null"]) == "union"
        assert _AvroDiff._name({"type": "fixed", "name": "F"}) == "F"
        assert self.run(["null", "string"], ["null", "string", "int"], "backward") == []


class TestGateWrappers:
    def test_run_contract_diff(self, tmp_path: Path) -> None:
        (tmp_path / "old.json").write_text(json.dumps(schema(a={"type": "string"})))
        (tmp_path / "new.json").write_text(json.dumps(schema()))
        result = run_contract_diff("old.json", "new.json", tmp_path, "output", "full")
        assert result.summary == {"kind": "jsonschema", "role": "output", "breaking": 1}
        assert not result.passed
        (tmp_path / "a.avsc").write_text(json.dumps(record("A")))
        avro = run_contract_diff("a.avsc", "a.avsc", tmp_path, "output", "backward")
        assert avro.summary["role"] == "backward" and avro.passed

    def test_run_contract_check(self, tmp_path: Path) -> None:
        def put(rel: str, doc) -> None:
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(doc), encoding="utf-8")

        item_v2 = schema(id={"type": "string"})
        put("normalize/contracts/item.json", item_v2)
        put("store/contracts/item.json", item_v2)
        put("delivery/contracts/item.json", schema(id={"type": "string"},
                                                   legacy={"type": "string"}))
        put("ingest/contracts/raw.json", schema(x={"type": "string"}))
        put("normalize/contracts/raw.json", schema())
        manifest = {
            "repos": {"ingest": "ingest", "normalize": "normalize", "store": "store",
                      "delivery": "delivery", "ghost": "ghost", "abs": str(tmp_path / "store")},
            "contracts": [
                {"name": "item", "provider": {"repo": "normalize", "path": "contracts/item.json"},
                 "consumers": [{"repo": "store", "path": "contracts/item.json"},
                               {"repo": "delivery", "path": "contracts/item.json"},
                               {"repo": "ghost", "path": "x.json"},
                               {"repo": "store", "path": "contracts/none.json"}]},
                {"name": "raw", "role": "output",
                 "provider": {"repo": "ingest", "path": "contracts/raw.json"},
                 "consumers": [{"repo": "normalize", "path": "contracts/raw.json"}]},
                {"name": "lost", "provider": {"repo": "ghost", "path": "x"}},
                {"name": "nofile", "provider": {"repo": "ingest", "path": "nope.json"}},
            ],
        }
        put("coord/contracts.json", manifest)
        result = run_contract_check(tmp_path / "coord/contracts.json", tmp_path)
        found = sorted(f.code for f in result.findings)
        assert found == ["consumer_breaking_drift", "consumer_contract_missing",
                         "consumer_stale_copy", "provider_contract_missing",
                         "repo_not_checked_out", "repo_not_checked_out"]
        drift = next(f for f in result.findings if f.code == "consumer_breaking_drift")
        assert drift.path == "item -> delivery" and "property_removed" in drift.message
        order = result.summary["merge_order"]
        assert order.index("ingest") < order.index("normalize") < order.index("store")

        manifest["contracts"] = manifest["contracts"][1:2]
        put("coord/contracts.json", manifest)
        stale = run_contract_check(tmp_path / "coord/contracts.json", tmp_path, strict=True)
        assert [f.code for f in stale.findings] == ["consumer_stale_copy"] and not stale.passed

    def test_cycle_detection(self) -> None:
        order, cyclic = _merge_order({"a": {"b"}, "b": {"a"}, "c": set()})
        assert order == ["c"] and cyclic == {"a", "b"}

    def test_contract_check_reports_cycle(self, tmp_path: Path) -> None:
        for repo_name in ("a", "b"):
            (tmp_path / repo_name).mkdir()
            (tmp_path / repo_name / "c.json").write_text("{}")
        manifest = {"repos": {"a": "a", "b": "b"}, "contracts": [
            {"name": "ab", "provider": {"repo": "a", "path": "c.json"},
             "consumers": [{"repo": "b", "path": "c.json"}]},
            {"name": "ba", "provider": {"repo": "b", "path": "c.json"},
             "consumers": [{"repo": "a", "path": "c.json"}]}]}
        (tmp_path / "m.json").write_text(json.dumps(manifest))
        result = run_contract_check(tmp_path / "m.json", None)
        assert [f.code for f in result.findings] == ["contract_cycle"]
