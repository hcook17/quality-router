"""The generated-OpenAPI YAML subset loader (springdoc / swagger-core / SnakeYAML output)."""

from __future__ import annotations

import math

import pytest

from quality_router.harness.yamlsubset import YamlSubsetError, loads

SPRINGDOC = """\
openapi: 3.0.1
info:
  title: Content API
  description: A Spring Boot service that delivers course content to front
    ends
  version: SNAPSHOT
tags:
- name: Item Controller
  description: Operations for items.
paths:
  /api/item/{id}:
    get:
      summary: "Get a skill mapping by concept id, skill id, and collection\\
        \\ id"
      parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string
      responses:
        "200":
          content:
            '*/*':
              schema:
                $ref: '#/components/schemas/Item'
        "404":
          description: 'it''s missing'
  ? /api/a/very/long/path/{that}/snakeyaml/emits/as/an/explicit/key
  : get:
      responses:
        "200":
          description: ok
components:
  schemas:
    Item:
      required:
      - id
      type: object
      properties:
        id:
          type: string
        count:
          type: integer
          format: int32
          minimum: 0
        extra: {}
"""


def test_springdoc_document() -> None:
    doc = loads(SPRINGDOC)
    assert doc["info"]["description"] == ("A Spring Boot service that delivers course "
                                          "content to front ends")
    op = doc["paths"]["/api/item/{id}"]["get"]
    assert op["summary"] == ("Get a skill mapping by concept id, skill id, and "
                             "collection id")
    assert op["parameters"] == [{"name": "id", "in": "path", "required": True,
                                 "schema": {"type": "string"}}]
    assert op["responses"]["200"]["content"]["*/*"]["schema"] == {
        "$ref": "#/components/schemas/Item"}
    assert op["responses"]["404"]["description"] == "it's missing"
    long_key = "/api/a/very/long/path/{that}/snakeyaml/emits/as/an/explicit/key"
    assert doc["paths"][long_key] == {"get": {"responses": {"200": {"description": "ok"}}}}
    item = doc["components"]["schemas"]["Item"]
    assert item["required"] == ["id"] and item["properties"]["count"]["minimum"] == 0
    assert item["properties"]["extra"] == {}
    assert doc["tags"] == [{"name": "Item Controller",
                            "description": "Operations for items."}]


@pytest.mark.parametrize("text, value", [
    ("a: ~", None), ("a: null", None), ("a:", None), ("a: True", True), ("a: false", False),
    ("a: 42", 42), ("a: -7", -7), ("a: 0x1F", 31), ("a: 0o17", 15),
    ("a: 1.5", 1.5), ("a: 1e3", 1000.0), ("a: .inf", math.inf), ("a: -.inf", -math.inf),
    ("a: '3'", "3"), ('a: "x\\ty\\u00e9\\x41\\/\\\\"', "x\tyéA/\\"), ("a: b # note", "b"),
    ("a: []", []), ("a: http://x:8080/y", "http://x:8080/y"), ("a: 1\n  - b", "1 - b"),
    ("a: 'one\n  two\n\n  three'", "one two\nthree"), ("a: plain\n\n  next", "plain\nnext"),
    ("a: 'it''s'", "it's"),
])
def test_scalars(text: str, value: object) -> None:
    assert loads(text) == {"a": value}


@pytest.mark.parametrize("text, value", [
    ("- 1\n- two", [1, "two"]), ("a:\n  - x\n  -\n    b: 1", {"a": ["x", {"b": 1}]}),
    ("- - 1\n  - 2", [[1, 2]]), ("---\na: 1\n...", {"a": 1}), ("# c\n\na: 1", {"a": 1}),
    ("", None), ('"q k": 1', {"q k": 1}), ("? k\n: v", {"k": "v"}),
    ("? k\n:\n  b: 1", {"k": {"b": 1}}), ("? k", {"k": None}),
    ("? k\nz: 1", {"k": None, "z": 1}), ("scalar", "scalar"), ("a:\n  b:\nc: 1", {
        "a": {"b": None}, "c": 1}),
])
def test_shapes(text: str, value: object) -> None:
    assert loads(text) == value


def test_nan() -> None:
    assert math.isnan(loads("a: .nan")["a"])


@pytest.mark.parametrize("text, message", [
    ("a: &x 1", "anchors"), ("a: *x", "anchors"), ("a: !tag 1", "anchors"),
    ("a: |\n  text", "anchors"), ("a: [1, 2]", "flow"), ("a: {b: 1}", "flow"),
    ("a: 1\n---\nb: 2", "multiple documents"), ("a:\n\t b: 1", "tab"),
    ("a: 1\na: 2", "duplicate"), ("? k\n: v\n? k\n: w", "duplicate"),
    ("a: 'open", "unterminated"), ('a: "open', "unterminated"), ("a: 'x' y", "trailing"),
    ('a: "\\q"', "unsupported escape"), ('a: "\\u12"', "short"),
    ("a:\n  b: 1\n c: 2", "unexpected indentation"), ("a: b: c", "inside a plain scalar"),
    ("? - x\n: v", "scalar explicit"), ("? a: b\n: v", "scalar explicit"),
    ("a: 1\n...\nb: 2", "multiple documents"), ("a:\n  b: 1\n  - c", "expected"),
])
def test_rejects_outside_subset(text: str, message: str) -> None:
    with pytest.raises(YamlSubsetError, match=message):
        loads(text)
