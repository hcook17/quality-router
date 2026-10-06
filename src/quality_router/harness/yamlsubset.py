"""Strict loader for the block-YAML subset that OpenAPI generators emit (stdlib only).

springdoc / swagger-core / Jackson YAML output uses block mappings and
sequences, plain / single- / double-quoted scalars (possibly folded over
several lines), explicit `? key` / `: value` entries for long keys, and empty
`{}` / `[]`. That is all this accepts. Anchors,
aliases, tags, block scalars (`|`, `>`), non-empty flow collections,
multiple documents and tab indentation raise YamlSubsetError with a line
number, so an unsupported file fails loudly instead of diffing wrongly.
Scalars resolve with the YAML 1.2 core schema (null, bool, int, float, str).
"""

from __future__ import annotations

import re
from typing import Any

_INT = re.compile(r"[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+")
_FLOAT = re.compile(r"[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?")
_PLAIN_KEY = re.compile(r"([^\s'\"#\-?:,\[\]{}&*!|>%@`][^#]*?|-[^\s#][^#]*?)\s*:(?:\s+|$)")
_UNSUPPORTED_START = ("&", "*", "!", "|", ">", "%", "@", "`")


class YamlSubsetError(ValueError):
    pass


class _Line:
    __slots__ = ("indent", "text", "number", "gap")

    def __init__(self, indent: int, text: str, number: int, gap: int = 0) -> None:
        self.indent, self.text, self.number, self.gap = indent, text, number, gap


def loads(text: str) -> Any:
    lines: list[_Line] = []
    gap = 0
    ended = False
    for number, raw in enumerate(text.splitlines(), 1):
        body = raw.rstrip()
        stripped = body.lstrip(" ")
        if not stripped:
            gap += 1
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("\t") or "\t" in body[:len(body) - len(stripped)]:
            raise YamlSubsetError(f"line {number}: tab indentation")
        if ended or (stripped == "---" and body == stripped and lines):
            raise YamlSubsetError(f"line {number}: multiple documents")
        if stripped in ("---", "...") and body == stripped:
            ended = stripped == "..."
            continue
        lines.append(_Line(len(body) - len(stripped), stripped, number, gap))
        gap = 0
    if not lines:
        return None
    parser = _Parser(lines)
    value = parser.block(0, lines[0].indent)
    if parser.i < len(lines):
        line = lines[parser.i]
        raise YamlSubsetError(f"line {line.number}: unexpected indentation")
    return value


class _Parser:
    def __init__(self, lines: list[_Line]) -> None:
        self.lines = lines
        self.i = 0

    def block(self, i: int, indent: int) -> Any:
        self.i = i
        line = self.lines[i]
        if line.text == "-" or line.text.startswith("- "):
            return self.sequence(indent)
        if _key(line) is None and not line.text.startswith("? "):
            self.i = i + 1
            return self.scalar_at(line, line.text, indent - 1)
        return self.mapping(indent)

    def mapping(self, indent: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.indent != indent or line.text == "-" or line.text.startswith("- "):
                break
            if line.text.startswith("? "):
                key, value = self.explicit_entry(line, indent)
                if key in out:
                    raise YamlSubsetError(f"line {line.number}: duplicate key {key!r}")
                out[key] = value
                continue
            found = _key(line)
            if found is None:
                raise YamlSubsetError(f"line {line.number}: expected 'key: value'")
            key, rest = found
            if key in out:
                raise YamlSubsetError(f"line {line.number}: duplicate key {key!r}")
            self.i += 1
            out[key] = self.value_after(line, rest, indent)
        return out

    def sequence(self, indent: int) -> list[Any]:
        out: list[Any] = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.indent != indent or not (line.text == "-" or line.text.startswith("- ")):
                break
            content = line.text[1:].lstrip(" ")
            if not content:
                self.i += 1
                out.append(self.nested(indent, line))
                continue
            offset = len(line.text) - len(content)
            if content.startswith("- ") or _key(_Line(0, content, line.number)) is not None:
                self.lines[self.i] = _Line(indent + offset, content, line.number)
                out.append(self.block(self.i, indent + offset))
                continue
            self.i += 1
            out.append(self.scalar_at(line, content, indent))
        return out

    def explicit_entry(self, line: _Line, indent: int) -> tuple[str, Any]:
        """`? long key` / `: value`, which SnakeYAML emits for keys over 128 characters."""
        self.i += 1
        content = line.text[2:].lstrip(" ")
        if content == "-" or content.startswith("- ") or _key(_Line(0, content, 0)):
            raise YamlSubsetError(f"line {line.number}: only scalar explicit keys are supported")
        key = self.scalar_at(line, content, indent)
        if not isinstance(key, str):
            raise YamlSubsetError(f"line {line.number}: only scalar explicit keys are supported")
        if self.i >= len(self.lines):
            return key, None
        colon = self.lines[self.i]
        if colon.indent != indent or not (colon.text == ":" or colon.text.startswith(": ")):
            return key, None
        content = colon.text[1:].lstrip(" ")
        if not content:
            self.i += 1
            return key, self.nested(indent, colon)
        offset = len(colon.text) - len(content)
        self.lines[self.i] = _Line(indent + offset, content, colon.number)
        return key, self.block(self.i, indent + offset)

    def value_after(self, line: _Line, rest: str, indent: int) -> Any:
        if rest:
            return self.scalar_at(line, rest, indent)
        if self.i < len(self.lines):
            nxt = self.lines[self.i]
            if nxt.indent == indent and (nxt.text == "-" or nxt.text.startswith("- ")):
                return self.sequence(indent)
        return self.nested(indent, line)

    def nested(self, indent: int, line: _Line) -> Any:
        if self.i < len(self.lines) and self.lines[self.i].indent > indent:
            return self.block(self.i, self.lines[self.i].indent)
        return None

    def scalar_at(self, line: _Line, text: str, indent: int) -> Any:
        """Scalar starting on `line`; continuation lines are those indented past `indent`."""
        parts = [(0, text)]
        while (self.i < len(self.lines) and self.lines[self.i].indent > indent
               and not _closed(" ".join(p for _, p in parts))):
            parts.append((self.lines[self.i].gap, self.lines[self.i].text))
            self.i += 1
        return _scalar(_fold(parts, text[:1] == '"'), line.number)


def _fold(parts: list[tuple[int, str]], double: bool) -> str:
    """YAML line folding: a break is a space, n blank lines are n newlines, and in
    double quotes a trailing backslash escapes the break."""
    out = parts[0][1]
    for gap, text in parts[1:]:
        trailing = len(out) - len(out.rstrip("\\"))
        if double and trailing % 2 == 1:
            out = out[:-1] + "\n" * gap + text
        else:
            out = out.rstrip(" ") + ("\n" * gap if gap else " ") + text
    return out


def _closed(text: str) -> bool:
    """False while a quoted scalar is still open (it continues on the next line)."""
    if text[:1] == "'":
        body = text[1:].replace("''", "")
        return "'" in body
    if text[:1] == '"':
        return re.search(r'(?<!\\)(?:\\\\)*"', text[1:]) is not None
    return False


def _key(line: _Line) -> tuple[str, str] | None:
    text = line.text
    if text[:1] in "'\"":
        end = _quote_end(text)
        if end is None or not re.match(r"\s*:(?:\s|$)", text[end + 1:]):
            return None
        colon = text.index(":", end + 1)
        return str(_scalar(text[:end + 1], line.number)), text[colon + 1:].strip()
    match = _PLAIN_KEY.match(text)
    if match is None:
        return None
    return match.group(1).strip(), text[match.end():].strip()


def _quote_end(text: str) -> int | None:
    quote, i = text[0], 1
    while i < len(text):
        if quote == "'" and text[i] == "'":
            if text[i + 1:i + 2] == "'":
                i += 2
                continue
            return i
        if quote == '"' and text[i] == "\\":
            i += 2
            continue
        if quote == '"' and text[i] == '"':
            return i
        i += 1
    return None


def _scalar(text: str, number: int) -> Any:
    text = text.strip()
    if text in ("{}", "[]"):
        return {} if text == "{}" else []
    if text[:1] in "[{":
        raise YamlSubsetError(f"line {number}: flow collections are not supported")
    if text[:1] in _UNSUPPORTED_START:
        raise YamlSubsetError(f"line {number}: anchors, aliases, tags and block scalars "
                              "are not supported")
    if text[:1] == "'":
        if _quote_end(text) != len(text) - 1:
            raise YamlSubsetError(f"line {number}: unterminated or trailing text after '...'")
        return text[1:-1].replace("''", "'")
    if text[:1] == '"':
        if _quote_end(text) != len(text) - 1:
            raise YamlSubsetError(f'line {number}: unterminated or trailing text after "..."')
        return _unescape_double(text[1:-1], number)
    if " #" in text:
        text = text.split(" #", 1)[0].rstrip()
    if ": " in text or text.endswith(":"):
        raise YamlSubsetError(f"line {number}: ': ' inside a plain scalar (quote it)")
    return _resolve(text)


_ESCAPES = {"0": "\0", "a": "\a", "b": "\b", "t": "\t", "\t": "\t", "n": "\n", "v": "\v",
            "f": "\f", "r": "\r", "e": "\x1b", " ": " ", '"': '"', "/": "/", "\\": "\\",
            "N": "\x85", "_": "\xa0", "L": "\u2028", "P": "\u2029"}
_HEX = {"x": 2, "u": 4, "U": 8}


def _unescape_double(body: str, number: int) -> str:
    out: list[str] = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        code = body[i + 1:i + 2]
        if code in _ESCAPES:
            out.append(_ESCAPES[code])
            i += 2
        elif code in _HEX and re.fullmatch(r"[0-9a-fA-F]+", body[i + 2:i + 2 + _HEX[code]] or "-"):
            digits = body[i + 2:i + 2 + _HEX[code]]
            if len(digits) != _HEX[code]:
                raise YamlSubsetError(f"line {number}: short \\{code} escape")
            out.append(chr(int(digits, 16)))
            i += 2 + _HEX[code]
        else:
            raise YamlSubsetError(f"line {number}: unsupported escape \\{code}")
    return "".join(out)


def _resolve(text: str) -> Any:
    if text in ("", "~", "null", "Null", "NULL"):
        return None
    if text in ("true", "True", "TRUE"):
        return True
    if text in ("false", "False", "FALSE"):
        return False
    if _INT.fullmatch(text):
        if text.startswith(("0o", "0x")):
            return int(text[2:], 8 if text[1] == "o" else 16)
        return int(text)
    if _FLOAT.fullmatch(text) and any(c.isdigit() for c in text):
        return float(text)
    if text in (".inf", ".Inf", ".INF", "+.inf"):
        return float("inf")
    if text in ("-.inf", "-.Inf", "-.INF"):
        return float("-inf")
    if text in (".nan", ".NaN", ".NAN"):
        return float("nan")
    return text
