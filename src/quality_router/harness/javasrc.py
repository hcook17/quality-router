"""Minimal Java source scanning: blank literals/comments, line lookup, brace matching.

Not a parser. Good enough to find annotated methods and catch blocks in
conventional JUnit/Spring code; text blocks and unicode escapes are treated
as ordinary characters.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass


def blank_strings_and_comments(source: str) -> str:
    """Replace string/char literals and comments with spaces, keeping newlines and offsets."""
    out = list(source)
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "/":
            j = source.find("\n", i)
            j = n if j < 0 else j
        elif ch == "/" and nxt == "*":
            j = source.find("*/", i + 2)
            j = n if j < 0 else j + 2
        elif ch in "\"'":
            j = i + 1
            while j < n and source[j] != ch and source[j] != "\n":
                j += 2 if source[j] == "\\" else 1
            j = min(j + 1, n)
        else:
            i += 1
            continue
        for k in range(i, j):
            if out[k] != "\n":
                out[k] = " "
        i = j
    return "".join(out)


def line_lookup(text: str) -> Callable[[int], int]:
    """Return offset -> 1-based line number."""
    starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]

    def line_of(offset: int) -> int:
        lo, hi = 0, len(starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    return line_of


def matching_brace(text: str, open_index: int) -> int:
    """Index of the `}` closing the `{` at open_index (or len-1 if unbalanced)."""
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(text) - 1


_CATCH = re.compile(r"\bcatch\s*\(")


def catch_block_lines(source: str) -> set[int]:
    """1-based line numbers inside `catch (...) { ... }` blocks, including the catch line."""
    text = blank_strings_and_comments(source)
    line_of = line_lookup(text)
    result: set[int] = set()
    for match in _CATCH.finditer(text):
        open_brace = text.find("{", match.end())
        if open_brace < 0:
            continue
        end = matching_brace(text, open_brace)
        result.update(range(line_of(match.start()), line_of(end) + 1))
    return result


TEST_ANNOTATIONS = ("Test", "ParameterizedTest", "RepeatedTest", "TestFactory",
                    "TestTemplate", "Property", "Example")
_ANNOTATION = re.compile(r"@(?:org\.junit(?:\.jupiter\.api|\.jupiter\.params)?\.)?("
                         + "|".join(TEST_ANNOTATIONS) + r")\b(\s*\([^)]*\))?")
_IDENT_BEFORE_PAREN = re.compile(r"(@?)\b(\w+)\s*$")


def _signature(text: str, start: int) -> tuple[str, int] | None:
    """From `start`, find (method name, index of body `{`) at paren depth 0."""
    depth = 0
    name = ""
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "(":
            if depth == 0 and not name:
                ident = _IDENT_BEFORE_PAREN.search(text, start, i)
                if ident and not ident.group(1):
                    name = ident.group(2)
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and ch == ";":
            return None
        elif depth == 0 and ch == "{":
            return (name, i) if name else None
    return None


@dataclass(frozen=True)
class TestMethod:
    __test__ = False

    name: str
    start_line: int
    end_line: int
    body: str
    annotation_args: str


def test_methods(source: str) -> list[TestMethod]:
    """JUnit 4/5 (and jqwik) annotated test methods with their blanked bodies."""
    text = blank_strings_and_comments(source)
    line_of = line_lookup(text)
    methods: list[TestMethod] = []
    for ann in _ANNOTATION.finditer(text):
        args = source[ann.start(2):ann.end(2)] if ann.group(2) else ""
        found = _signature(text, ann.end())
        if found is None:
            continue
        name, open_brace = found
        close = matching_brace(text, open_brace)
        methods.append(TestMethod(
            name=name,
            start_line=line_of(ann.start()),
            end_line=line_of(close),
            body=text[open_brace + 1:close],
            annotation_args=args,
        ))
    return methods
