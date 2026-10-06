"""Harness-research knowledge base ETL (stdlib only).

Stages: harvest -> transform -> select -> fulltext -> batches -> load -> report.
Raw caches live under raw/ (gitignored); committed outputs are JSONL, reviews/,
and generated report tables. kb.sqlite is rebuilt by `load`.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
ATOM = RAW / "atom"
TEXT = RAW / "text"
SIGNALS = ROOT / "signals"
REVIEWS = ROOT / "reviews"
BATCHES = ROOT / "batches"
TAXONOMY = json.loads((ROOT / "taxonomy.json").read_text())
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
UA = "harness-kb/0.1 (research ETL; contact via repo)"
API = "https://export.arxiv.org/api/query"
ARXIV_DELAY_S = 3.1

CORE = re.compile(r"\b(LLMs?|large language models?|language models?|agents?|agentic|GPT|Claude)\b", re.I)
SOFTWARE = re.compile(
    r"\b(code|coding|software|repositor(y|ies)|program(s|ming)?|developers?|pull requests?|"
    r"APIs?|pipelines?|engineering|bugs?|tests?|compil\w+|devops)\b",
    re.I,
)
VENDORS = [
    "Anthropic", "OpenAI", "Google", "DeepMind", "Microsoft", "GitHub", "Meta", "Amazon", "AWS",
    "Alibaba", "Qwen", "ByteDance", "Tencent", "Huawei", "Baidu", "DeepSeek", "Moonshot", "Zhipu",
    "Mistral", "Cohere", "NVIDIA", "IBM", "Salesforce", "JetBrains", "Cursor", "Anysphere",
    "Sourcegraph", "Replit", "Cognition", "All Hands", "Databricks", "Snowflake", "Atlassian",
    "SAP", "Oracle", "Nous Research", "xAI", "Ant Group", "Kuaishou", "Xiaomi", "Samsung",
]


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as exc:  # network flake or 429/503
            code = getattr(exc, "code", None)
            if attempt == 4 or (code is not None and 400 <= code < 500 and code != 429):
                raise
            wait = 4 * 2**attempt
            print(f"  retry {attempt + 1} after {wait}s: {exc}", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def build_query(topic: dict) -> str:
    phrases = " OR ".join(f'ti:"{p}" OR abs:"{p}"' for p in topic["phrases"])
    cats = " OR ".join(f"cat:{c}" for c in TAXONOMY["categories"])
    w = TAXONOMY["window"]
    return f"({phrases}) AND ({cats}) AND submittedDate:[{w['from']} TO {w['to']}]"


def cmd_harvest(args: argparse.Namespace) -> None:
    ATOM.mkdir(parents=True, exist_ok=True)
    for topic in TAXONOMY["topics"]:
        if args.only and topic["id"] not in args.only:
            continue
        for page in range(args.pages):
            out = ATOM / f"{topic['id']}_p{page}.xml"
            if out.exists() and not args.force:
                continue
            params = {
                "search_query": build_query(topic),
                "start": page * args.per_page,
                "max_results": args.per_page,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            url = API + "?" + urllib.parse.urlencode(params)
            data = _get(url)
            out.write_bytes(data)
            total = re.search(rb"<opensearch:totalResults>(\d+)<", data)
            n = total.group(1).decode() if total else "?"
            print(f"{topic['id']} p{page}: total={n} {topic['name']}")
            time.sleep(ARXIV_DELAY_S)


def _parse_entry(e: ET.Element) -> dict:
    raw_id = e.findtext("a:id", default="", namespaces=NS).rsplit("/abs/", 1)[-1]
    m = re.match(r"(.+?)(v(\d+))?$", raw_id)
    base, ver = m.group(1), int(m.group(3) or 1)
    authors = []
    for a in e.findall("a:author", NS):
        authors.append({
            "name": a.findtext("a:name", default="", namespaces=NS).strip(),
            "affiliation": [x.text.strip() for x in a.findall("arxiv:affiliation", NS) if x.text],
        })
    prim = e.find("arxiv:primary_category", NS)
    return {
        "arxiv_id": base,
        "version": ver,
        "title": " ".join(e.findtext("a:title", default="", namespaces=NS).split()),
        "abstract": " ".join(e.findtext("a:summary", default="", namespaces=NS).split()),
        "authors": authors,
        "published": e.findtext("a:published", default="", namespaces=NS)[:10],
        "updated": e.findtext("a:updated", default="", namespaces=NS)[:10],
        "primary_category": prim.get("term") if prim is not None else "",
        "categories": [c.get("term") for c in e.findall("a:category", NS)],
        "comment": " ".join((e.findtext("arxiv:comment", default="", namespaces=NS) or "").split()),
        "journal_ref": e.findtext("arxiv:journal_ref", default="", namespaces=NS) or "",
        "doi": e.findtext("arxiv:doi", default="", namespaces=NS) or "",
    }


def relevance(p: dict, topic: dict) -> float:
    text = f"{p['title']} {p['abstract']}"
    if not CORE.search(text):
        return 0.0
    if topic["cluster"] in {"C11", "C09", "C10"} and not SOFTWARE.search(text):
        return 0.0
    score = 1.0
    for ph in topic["phrases"]:
        pat = re.compile(re.escape(ph), re.I)
        score += 3.0 * len(pat.findall(p["title"])) + 1.0 * min(3, len(pat.findall(p["abstract"])))
    score += 0.5 * min(6, len(SOFTWARE.findall(text)))
    if re.search(r"\b(coding|software engineering|SWE)\b.{0,20}\bagents?\b", text, re.I):
        score += 2.0
    return round(score, 2)


def cmd_transform(args: argparse.Namespace) -> None:
    papers: dict[str, dict] = {}
    topic_by_id = {t["id"]: t for t in TAXONOMY["topics"]}
    for f in sorted(ATOM.glob("T*_p*.xml")):
        tid = f.name.split("_")[0]
        topic = topic_by_id[tid]
        root = ET.fromstring(f.read_bytes())
        page = int(f.stem.split("_p")[1])
        for rank, e in enumerate(root.findall("a:entry", NS)):
            p = _parse_entry(e)
            if not p["title"]:
                continue
            rel = relevance(p, topic)
            cur = papers.setdefault(p["arxiv_id"], {**p, "topic_hits": {}})
            if p["version"] > cur["version"]:
                cur.update({k: v for k, v in p.items()})
            api_rank = page * 100 + rank
            prev = cur["topic_hits"].get(tid)
            if prev is None or api_rank < prev["api_rank"]:
                cur["topic_hits"][tid] = {"api_rank": api_rank, "relevance": rel}
    out = ROOT / "papers.jsonl"
    with out.open("w") as fh:
        for p in sorted(papers.values(), key=lambda x: x["arxiv_id"]):
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    kept = sum(1 for p in papers.values() if any(h["relevance"] > 0 for h in p["topic_hits"].values()))
    print(f"papers: {len(papers)} unique, {kept} pass relevance gate -> {out.name}")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def cmd_select(args: argparse.Namespace) -> None:
    papers = load_jsonl(ROOT / "papers.jsonl")
    chosen: dict[str, dict] = {}
    for topic in TAXONOMY["topics"]:
        tid = topic["id"]
        pool = [p for p in papers if p["topic_hits"].get(tid, {}).get("relevance", 0) > 0]
        pool.sort(key=lambda p: (-(p["topic_hits"][tid]["relevance"] - 0.02 * p["topic_hits"][tid]["api_rank"]),))
        n = 0
        for p in pool:
            if n >= args.per_topic:
                break
            if p["arxiv_id"] in chosen:
                chosen[p["arxiv_id"]]["selected_for"].append(tid)
                continue
            chosen[p["arxiv_id"]] = {"arxiv_id": p["arxiv_id"], "version": p["version"],
                                     "title": p["title"], "selected_for": [tid]}
            n += 1
    out = ROOT / "candidates.jsonl"
    with out.open("w") as fh:
        for c in sorted(chosen.values(), key=lambda x: x["arxiv_id"]):
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    covered = {t for c in chosen.values() for t in c["selected_for"]}
    print(f"candidates: {len(chosen)} papers covering {len(covered)}/{len(TAXONOMY['topics'])} topics")


class _Text(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "annotation", "annotation-xml", "button"}
    BLOCK = {"p", "div", "li", "tr", "br", "section", "figcaption", "table", "article"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0
        self.in_math = 0
        self.authors_depth = 0
        self.authors: list[str] = []
        self.stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag in self.SKIP:
            self.skip += 1
        if tag == "math":
            self.in_math += 1
            alt = a.get("alttext")
            if alt:
                self.out.append(f" {alt} ")
        if "ltx_authors" in cls and not self.authors_depth:
            self.authors_depth = 1
        elif self.authors_depth:
            self.authors_depth += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in self.BLOCK:
            self.out.append("\n")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag == "math" and self.in_math:
            self.in_math -= 1
        if self.authors_depth:
            self.authors_depth -= 1
        if re.fullmatch(r"h[1-6]", tag) or tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip or self.in_math:
            return
        self.out.append(data)
        if self.authors_depth:
            self.authors.append(data)

    def text(self) -> str:
        t = "".join(self.out)
        t = re.sub(r"[ \t\u00a0]+", " ", t)
        t = re.sub(r"\n\s*\n\s*\n+", "\n\n", t)
        return t.strip()


def _fulltext(pid: str, ver: int) -> tuple[str, str, str]:
    try:
        raw = _get(f"https://arxiv.org/html/{pid}v{ver}", timeout=90).decode("utf-8", "replace")
        if "ltx_document" in raw or "ltx_page_main" in raw:
            p = _Text()
            p.feed(raw)
            return p.text(), " ".join(" ".join(p.authors).split()), "html"
    except Exception as exc:
        print(f"  html failed {pid}: {exc}", file=sys.stderr)
    if shutil.which("pdftotext"):
        pdf = RAW / "pdf" / f"{pid}.pdf"
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(_get(f"https://arxiv.org/pdf/{pid}v{ver}", timeout=120))
        txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                             text=True, check=False).stdout
        head = "\n".join(txt.splitlines()[:40])
        return txt, " ".join(head.split()), "pdf"
    return "", "", "none"


def _section(lines: list[str], pattern: str, n: int = 40) -> str:
    rx = re.compile(pattern, re.I)
    for i, ln in enumerate(lines):
        if ln.startswith("#") and rx.search(ln):
            return "\n".join(lines[i:i + n]).strip()
    return ""


def front_matter(text: str) -> str:
    """Author/affiliation block: lines after the title heading and before the abstract."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines[:80]) if re.match(r"#{1,2} \S", ln)), 0)
    end = next((i for i, ln in enumerate(lines[start:start + 200], start)
                if re.search(r"\babstract\b", ln, re.I)), min(len(lines), start + 40))
    return " ".join(" ".join(lines[start + 1:end]).split())


def signals_for(pid: str, text: str, authors_block: str, meta: dict) -> dict:
    lines = text.splitlines()
    authors_block = front_matter(text) or authors_block
    heads = [(i + 1, ln.strip()) for i, ln in enumerate(lines) if ln.startswith("#")]
    vendor_hits = sorted({v for v in VENDORS if re.search(rf"\b{re.escape(v)}\b", authors_block)})
    gh = sorted(set(re.findall(r"https?://(?:www\.)?github\.com/[\w.\-]+/[\w.\-]+", text)))[:15]
    hf = sorted(set(re.findall(r"https?://huggingface\.co/[\w.\-]+/[\w.\-]+", text)))[:10]
    def count(rx: str) -> int:
        return len(re.findall(rx, text, re.I))
    return {
        "arxiv_id": pid,
        "fulltext_chars": len(text),
        "fulltext_lines": len(lines),
        "authors_block": authors_block[:1500],
        "vendor_affiliation_hits": vendor_hits,
        "n_authors": len(meta.get("authors", [])),
        "comment": meta.get("comment", ""),
        "journal_ref": meta.get("journal_ref", ""),
        "github_urls": gh,
        "hf_urls": hf,
        "headings": heads[:120],
        "acknowledgments": _section(lines, r"acknowledg|funding", 25)[:2500],
        "limitations": _section(lines, r"limitation|threats to validity", 40)[:4000],
        "ethics_coi": _section(lines, r"conflict|competing interest|disclosure|ethic|impact statement", 25)[:2000],
        "counts": {
            "self_reported": count(r"self-reported"),
            "llm_as_judge": count(r"LLM[- ]as[- ]a?[- ]?judge|GPT-4o? as (a )?judge|judged by"),
            "p_value_or_ci": count(r"p\s*[<=]\s*0\.\d|confidence interval|\b95% CI\b|bootstrap|Wilcoxon|t-test|Mann"),
            "seeds_or_runs": count(r"random seeds?|\bseeds\b|independent runs|repeated \d+ times|pass@\d"),
            "swe_bench": count(r"SWE-bench"),
            "contamination": count(r"contaminat|data leakage|memoriz"),
            "human_study": count(r"participants|user study|interview(s|ed)?|survey(ed)? \d+|randomi[sz]ed"),
            "java": count(r"\bJava\b"),
            "industrial": count(r"industrial|in production|deployed at|enterprise"),
        },
    }


def cmd_fulltext(args: argparse.Namespace) -> None:
    TEXT.mkdir(parents=True, exist_ok=True)
    SIGNALS.mkdir(parents=True, exist_ok=True)
    meta = {p["arxiv_id"]: p for p in load_jsonl(ROOT / "papers.jsonl")}
    for c in load_jsonl(ROOT / "candidates.jsonl"):
        pid = c["arxiv_id"]
        tfile, sfile = TEXT / f"{pid}.txt", SIGNALS / f"{pid}.json"
        if sfile.exists() and tfile.exists() and not args.force:
            if json.loads(sfile.read_text()).get("fulltext_source") != "none":
                continue
        text, authors_block, src = _fulltext(pid, c["version"])
        tfile.write_text(text)
        sig = signals_for(pid, text, authors_block, meta.get(pid, {}))
        sig["fulltext_source"] = src
        sfile.write_text(json.dumps(sig, indent=1, ensure_ascii=False))
        print(f"{pid} {src} {len(text)//1000}k vendors={sig['vendor_affiliation_hits']}")
        time.sleep(1.0)


def cmd_resignal(args: argparse.Namespace) -> None:
    meta = {p["arxiv_id"]: p for p in load_jsonl(ROOT / "papers.jsonl")}
    for sfile in sorted(SIGNALS.glob("*.json")):
        old = json.loads(sfile.read_text())
        pid = old["arxiv_id"]
        text = (TEXT / f"{pid}.txt").read_text()
        sig = signals_for(pid, text, "", meta.get(pid, {}))
        sig["fulltext_source"] = old.get("fulltext_source", "none")
        sfile.write_text(json.dumps(sig, indent=1, ensure_ascii=False))
    print(f"resignaled {len(list(SIGNALS.glob('*.json')))}")


def cmd_batches(args: argparse.Namespace) -> None:
    BATCHES.mkdir(exist_ok=True)
    for f in BATCHES.glob("batch_*.txt"):
        f.unlink()
    ids = [c["arxiv_id"] for c in load_jsonl(ROOT / "candidates.jsonl")
           if not (REVIEWS / f"{c['arxiv_id']}.json").exists()]
    for i in range(0, len(ids), args.size):
        (BATCHES / f"batch_{i // args.size:02d}.txt").write_text("\n".join(ids[i:i + args.size]) + "\n")
    print(f"{len(ids)} unreviewed -> {(len(ids) + args.size - 1) // args.size} batches")


REQUIRED = {
    "arxiv_id": str, "contribution_type": str, "summary": str, "claims": list, "patterns": list,
    "methodology": dict, "standards": dict, "biases": list, "coi": dict, "scores": dict,
    "verdict": str, "verdict_reason": str, "applicability": str, "conflicts_with": list,
}
CONTRIB = {"empirical", "benchmark", "system", "position", "survey", "theory", "replication", "dataset", "tool"}
VERDICTS = {"admit", "admit_with_caveats", "reject"}
STANCE = {"supports", "contradicts", "mixed", "introduces", "neutral"}
STRENGTH = {"strong", "moderate", "weak", "unsupported"}
SCORE_KEYS = {"rigor", "reproducibility", "generalizability", "relevance", "coi_risk"}


def validate(r: dict, known_patterns: set[str]) -> list[str]:
    errs = []
    for k, t in REQUIRED.items():
        if not isinstance(r.get(k), t):
            errs.append(f"missing/invalid {k}")
    if errs:
        return errs
    if r["contribution_type"] not in CONTRIB:
        errs.append(f"contribution_type {r['contribution_type']}")
    if r["verdict"] not in VERDICTS:
        errs.append(f"verdict {r['verdict']}")
    for s in SCORE_KEYS:
        v = r["scores"].get(s)
        if not isinstance(v, int) or not 0 <= v <= 5:
            errs.append(f"score {s}={v}")
    for p in r["patterns"]:
        if p.get("id") not in known_patterns or p.get("stance") not in STANCE:
            errs.append(f"pattern {p}")
    for c in r["claims"]:
        if c.get("strength") not in STRENGTH or not c.get("claim"):
            errs.append(f"claim {str(c)[:60]}")
    if r["coi"].get("severity") not in {"none", "low", "medium", "high"}:
        errs.append("coi.severity")
    return errs


def admission(r: dict) -> str:
    """Deterministic gate: the reviewer proposes a verdict; the gate can only tighten it."""
    s = r["scores"]
    if r["verdict"] == "reject" or s["rigor"] <= 1:
        return "rejected"
    if r["coi"]["severity"] == "high" and s["rigor"] <= 2:
        return "rejected"
    if r["verdict"] == "admit_with_caveats" or s["coi_risk"] >= 3 or s["rigor"] == 2:
        return "caveated"
    return "admitted"


def weight(r: dict, status: str) -> float:
    if status == "rejected":
        return 0.0
    s = r["scores"]
    w = (s["rigor"] / 5) * (0.6 + 0.4 * s["reproducibility"] / 5) * (1 - 0.12 * s["coi_risk"])
    return round(w * (0.6 if status == "caveated" else 1.0), 3)


AUDITS = ROOT / "audits"
_VORDER = {"admit": 0, "admit_with_caveats": 1, "reject": 2}
_SORDER = {"none": 0, "low": 1, "medium": 2, "high": 3}
_CORDER = {"strong": 3, "moderate": 2, "weak": 1, "unsupported": 0}


def merge_audit(r: dict, a: dict) -> dict:
    """Conservative merge of a blind second-opinion audit into a review."""
    r = json.loads(json.dumps(r))
    b = a.get("blind_scores", {})
    for k in ("rigor", "reproducibility", "generalizability", "relevance"):
        if isinstance(b.get(k), int):
            r["scores"][k] = min(r["scores"][k], b[k])
    if isinstance(b.get("coi_risk"), int):
        r["scores"]["coi_risk"] = max(r["scores"]["coi_risk"], b["coi_risk"])
    if a.get("blind_verdict") in _VORDER and _VORDER[a["blind_verdict"]] > _VORDER[r["verdict"]]:
        r["verdict_reason"] = f"[audit tightened {r['verdict']}->{a['blind_verdict']}] " + r["verdict_reason"]
        r["verdict"] = a["blind_verdict"]
    sev = a.get("blind_coi_severity")
    if sev in _SORDER and _SORDER[sev] > _SORDER[r["coi"]["severity"]]:
        r["coi"]["severity"] = sev
    disputed = {d.get("claim", "").strip(): d for d in a.get("claims_disputed", [])}
    for c in r["claims"]:
        d = disputed.get(c["claim"].strip())
        if d and d.get("proposed_strength") in _CORDER and _CORDER[d["proposed_strength"]] < _CORDER[c["strength"]]:
            c["strength"] = d["proposed_strength"]
            c["evidence"] = f"[audit: {d.get('reason', '')[:300]}] " + c.get("evidence", "")
    changes = {x.get("id"): x for x in a.get("pattern_stance_changes", []) if x.get("to") in STANCE}
    for p in r["patterns"]:
        if p["id"] in changes:
            p["note"] = f"[audit {p['stance']}->{changes[p['id']]['to']}: {changes[p['id']].get('reason', '')[:200]}] " + p.get("note", "")
            p["stance"] = changes[p["id"]]["to"]
    for b_ in a.get("missed_issues", []):
        r["biases"].append({"type": "other:audit_missed", "detail": str(b_)[:500]})
    return r


SCHEMA = """
CREATE TABLE papers(arxiv_id TEXT PRIMARY KEY, version INT, title TEXT, abstract TEXT, published TEXT,
  primary_category TEXT, authors TEXT, comment TEXT, journal_ref TEXT, n_topics INT);
CREATE TABLE topics(id TEXT PRIMARY KEY, cluster TEXT, name TEXT);
CREATE TABLE paper_topics(arxiv_id TEXT, topic_id TEXT, api_rank INT, relevance REAL, selected INT);
CREATE TABLE reviews(arxiv_id TEXT PRIMARY KEY, contribution_type TEXT, summary TEXT, verdict TEXT,
  status TEXT, weight REAL, rigor INT, reproducibility INT, generalizability INT, relevance INT,
  coi_risk INT, coi_severity TEXT, coi_json TEXT, methodology_json TEXT, standards_json TEXT,
  applicability TEXT, verdict_reason TEXT);
CREATE TABLE claims(arxiv_id TEXT, claim TEXT, evidence TEXT, strength TEXT, location TEXT);
CREATE TABLE pattern_evidence(arxiv_id TEXT, pattern_id TEXT, stance TEXT, note TEXT);
CREATE TABLE biases(arxiv_id TEXT, bias TEXT, detail TEXT);
CREATE TABLE conflicts(arxiv_id TEXT, other TEXT, detail TEXT);
CREATE TABLE patterns(id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE audits(arxiv_id TEXT PRIMARY KEY, agreement TEXT, blind_verdict TEXT, blind_json TEXT, note TEXT);
CREATE VIRTUAL TABLE fts USING fts5(arxiv_id UNINDEXED, title, abstract, summary, claims);
"""


def cmd_load(args: argparse.Namespace) -> None:
    db_path = ROOT / "kb.sqlite"
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    papers = {p["arxiv_id"]: p for p in load_jsonl(ROOT / "papers.jsonl")}
    selected = {c["arxiv_id"]: c for c in load_jsonl(ROOT / "candidates.jsonl")}
    db.executemany("INSERT INTO topics VALUES(?,?,?)",
                   [(t["id"], t["cluster"], t["name"]) for t in TAXONOMY["topics"]])
    db.executemany("INSERT INTO patterns VALUES(?,?)", list(TAXONOMY["patterns"].items()))
    for p in papers.values():
        db.execute("INSERT INTO papers VALUES(?,?,?,?,?,?,?,?,?,?)", (
            p["arxiv_id"], p["version"], p["title"], p["abstract"], p["published"],
            p["primary_category"], json.dumps(p["authors"]), p["comment"], p["journal_ref"],
            len(p["topic_hits"])))
        sel = set(selected.get(p["arxiv_id"], {}).get("selected_for", []))
        for tid, h in p["topic_hits"].items():
            db.execute("INSERT INTO paper_topics VALUES(?,?,?,?,?)",
                       (p["arxiv_id"], tid, h["api_rank"], h["relevance"], int(tid in sel)))
    known = set(TAXONOMY["patterns"])
    bad, counts = [], {"admitted": 0, "caveated": 0, "rejected": 0}
    for f in sorted(REVIEWS.glob("*.json")):
        try:
            r = json.loads(f.read_text())
        except json.JSONDecodeError as exc:
            bad.append((f.name, [f"json: {exc}"]))
            continue
        errs = validate(r, known)
        if errs:
            bad.append((f.name, errs))
            continue
        af = AUDITS / f.name
        if af.exists():
            a = json.loads(af.read_text())
            r = merge_audit(r, a)
            db.execute("INSERT INTO audits VALUES(?,?,?,?,?)", (r["arxiv_id"], a.get("agreement", ""),
                       a.get("blind_verdict", ""), json.dumps(a), a.get("note", "")))
        status = admission(r)
        counts[status] += 1
        s = r["scores"]
        db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            r["arxiv_id"], r["contribution_type"], r["summary"], r["verdict"], status, weight(r, status),
            s["rigor"], s["reproducibility"], s["generalizability"], s["relevance"], s["coi_risk"],
            r["coi"]["severity"], json.dumps(r["coi"]), json.dumps(r["methodology"]),
            json.dumps(r["standards"]), r["applicability"], r["verdict_reason"]))
        for c in r["claims"]:
            db.execute("INSERT INTO claims VALUES(?,?,?,?,?)", (r["arxiv_id"], c["claim"],
                       c.get("evidence", ""), c["strength"], c.get("location", "")))
        for p in r["patterns"]:
            db.execute("INSERT INTO pattern_evidence VALUES(?,?,?,?)",
                       (r["arxiv_id"], p["id"], p["stance"], p.get("note", "")))
        for b in r["biases"]:
            db.execute("INSERT INTO biases VALUES(?,?,?)", (r["arxiv_id"], b.get("type", ""), b.get("detail", "")))
        for c in r["conflicts_with"]:
            db.execute("INSERT INTO conflicts VALUES(?,?,?)", (r["arxiv_id"], c.get("arxiv_id", ""), c.get("detail", "")))
        meta = papers.get(r["arxiv_id"], {})
        db.execute("INSERT INTO fts VALUES(?,?,?,?,?)", (r["arxiv_id"], meta.get("title", ""),
                   meta.get("abstract", ""), r["summary"], " ".join(c["claim"] for c in r["claims"])))
    db.commit()
    print(f"papers={len(papers)} reviews_loaded={sum(counts.values())} {counts} invalid={len(bad)}")
    for name, errs in bad:
        print(f"  INVALID {name}: {'; '.join(errs[:4])}")


def cmd_report(args: argparse.Namespace) -> None:
    db = sqlite3.connect(ROOT / "kb.sqlite")
    q = db.execute
    out = ["# Generated KB tables", "", "Regenerate with `python3 etl.py load && python3 etl.py report`.", ""]
    tot = q("SELECT COUNT(*) FROM papers").fetchone()[0]
    rev = q("SELECT status, COUNT(*) FROM reviews GROUP BY status").fetchall()
    out += [f"Harvested unique papers: {tot}. Reviews by gate status: {dict(rev)}.", ""]
    out += ["## Pattern evidence matrix", "",
            "Weighted score = sum of review weights (rigor x reproducibility x COI discount; caveated x0.6; rejected 0).", "",
            "| Pattern | Supports | Contradicts | Mixed | Introduces | Weighted support | Weighted contra | Vendor-authored share |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for pid, name in q("SELECT id, name FROM patterns ORDER BY id"):
        rows = q("""SELECT pe.stance, r.weight, r.coi_severity FROM pattern_evidence pe
                    JOIN reviews r USING(arxiv_id) WHERE pe.pattern_id=?""", (pid,)).fetchall()
        if not rows:
            continue
        c = {s: sum(1 for x in rows if x[0] == s) for s in ("supports", "contradicts", "mixed", "introduces")}
        ws = sum(w for s, w, _ in rows if s in ("supports", "introduces"))
        wc = sum(w for s, w, _ in rows if s == "contradicts")
        vend = sum(1 for _, _, sev in rows if sev in ("medium", "high")) / len(rows)
        out.append(f"| {pid} {name} | {c['supports']} | {c['contradicts']} | {c['mixed']} | {c['introduces']} | "
                   f"{ws:.2f} | {wc:.2f} | {vend:.0%} |")
    out += ["", "## Bias frequency", "", "| Bias | Papers |", "| --- | --- |"]
    for b, n in q("SELECT bias, COUNT(DISTINCT arxiv_id) n FROM biases GROUP BY bias ORDER BY n DESC LIMIT 25"):
        out.append(f"| {b} | {n} |")
    out += ["", "## COI severity", "", "| Severity | Papers | Mean rigor |", "| --- | --- | --- |"]
    for sev, n, mr in q("SELECT coi_severity, COUNT(*), AVG(rigor) FROM reviews GROUP BY coi_severity"):
        out.append(f"| {sev} | {n} | {mr:.2f} |")
    out += ["", "## Contribution types", "", "| Type | Papers | Mean rigor | Rejected |", "| --- | --- | --- | --- |"]
    for t, n, mr, rj in q("""SELECT contribution_type, COUNT(*), AVG(rigor),
                             SUM(status='rejected') FROM reviews GROUP BY contribution_type ORDER BY 2 DESC"""):
        out.append(f"| {t} | {n} | {mr:.2f} | {rj} |")
    out += ["", "## Topic coverage", "", "| Topic | Harvested (pass gate) | Reviewed | Admitted+caveated |",
            "| --- | --- | --- | --- |"]
    for tid, name in q("SELECT id, name FROM topics ORDER BY id"):
        h = q("SELECT COUNT(*) FROM paper_topics WHERE topic_id=? AND relevance>0", (tid,)).fetchone()[0]
        rv = q("""SELECT COUNT(*), SUM(r.status!='rejected') FROM paper_topics pt JOIN reviews r USING(arxiv_id)
                  WHERE pt.topic_id=? AND pt.selected=1""", (tid,)).fetchone()
        out.append(f"| {tid} {name} | {h} | {rv[0]} | {rv[1] or 0} |")
    out += ["", "## Top-weighted admitted papers", "", "| arXiv | Title | Type | Rigor | COI | Weight |",
            "| --- | --- | --- | --- | --- | --- |"]
    for row in q("""SELECT r.arxiv_id, p.title, r.contribution_type, r.rigor, r.coi_severity, r.weight
                    FROM reviews r JOIN papers p USING(arxiv_id) WHERE r.status!='rejected'
                    ORDER BY r.weight DESC, r.relevance DESC LIMIT 40"""):
        out.append(f"| [{row[0]}](https://arxiv.org/abs/{row[0]}) | {row[1][:90]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |")
    out += ["", "## Rejected", "", "| arXiv | Title | Reason |", "| --- | --- | --- |"]
    for row in q("""SELECT r.arxiv_id, p.title, r.verdict_reason FROM reviews r JOIN papers p USING(arxiv_id)
                    WHERE r.status='rejected' ORDER BY r.arxiv_id"""):
        out.append(f"| [{row[0]}](https://arxiv.org/abs/{row[0]}) | {row[1][:80]} | {row[2][:160]} |")
    out += ["", "## Second-opinion audits", "", "| Agreement | Papers |", "| --- | --- |"]
    for ag, n in q("SELECT agreement, COUNT(*) FROM audits GROUP BY agreement ORDER BY 2 DESC"):
        out.append(f"| {ag} | {n} |")
    flips = q("""SELECT a.arxiv_id, p.title, a.blind_verdict, r.status FROM audits a JOIN papers p USING(arxiv_id)
                 JOIN reviews r USING(arxiv_id) WHERE a.agreement='major_disagreement'""").fetchall()
    if flips:
        out += ["", "Major disagreements (merged conservatively):", ""]
        out += [f"- [{x[0]}](https://arxiv.org/abs/{x[0]}) {x[1][:80]} — blind verdict `{x[2]}`, final `{x[3]}`" for x in flips]
    (ROOT / "kb_tables.md").write_text("\n".join(out) + "\n")

    ev = ["# Evidence ledger by pattern", "",
          "Non-rejected papers only, ordered by review weight. Notes are reviewer/auditor text.", ""]
    for pid, name in q("SELECT id, name FROM patterns ORDER BY id"):
        rows = q("""SELECT pe.arxiv_id, pe.stance, r.weight, r.rigor, r.coi_severity, p.title, pe.note
                    FROM pattern_evidence pe JOIN reviews r USING(arxiv_id) JOIN papers p USING(arxiv_id)
                    WHERE pe.pattern_id=? AND r.status!='rejected' AND pe.stance!='neutral'
                    ORDER BY r.weight DESC""", (pid,)).fetchall()
        if not rows:
            continue
        ev += [f"## {pid} {name}", "", "| arXiv | Stance | Weight | Rigor | COI | Title | Note |",
               "| --- | --- | --- | --- | --- | --- | --- |"]
        for a_id, st, w, rg, coi, title, note in rows:
            note = " ".join((note or "").split()).replace("|", "/")[:260]
            ev.append(f"| [{a_id}](https://arxiv.org/abs/{a_id}) | {st} | {w} | {rg} | {coi} | {title[:70]} | {note} |")
        ev.append("")
    (ROOT / "kb_evidence.md").write_text("\n".join(ev) + "\n")
    print("wrote kb_tables.md, kb_evidence.md")


LANDSCAPE = {
    "P01 instruction files": r"AGENTS\.md|CLAUDE\.md|cursor ?rules|instruction files?|context files?",
    "P02 skills": r"\bskills?\b.{0,30}\b(agent|library|SKILL\.md)|SKILL\.md|agent skills",
    "P04 MCP": r"Model Context Protocol|\bMCP\b",
    "P06 code RAG/embeddings": r"retrieval[- ]augmented|\bRAG\b|embedding[- ]based retrieval|vector (store|database)",
    "P07 code graph": r"code graph|knowledge graph|call graph|dependency graph",
    "P08 compaction": r"compaction|context compression|summariz\w+ (the )?(history|context|trajectory)",
    "P09 memory": r"\bmemory\b",
    "P11 multi-agent": r"multi-agent|multiagent",
    "P14 spec-driven": r"spec(ification)?-driven|spec-first|specification first",
    "P15 TDD": r"test-driven|\bTDD\b",
    "P16 execution feedback": r"execution feedback|test feedback|run(ning)? (the )?tests|unit tests? (as|for) (feedback|verification)",
    "P17 static analysis": r"static analysis|linter|compiler (feedback|errors?)",
    "P18 LLM judge": r"LLM[- ]as[- ]a?[- ]?judge|LLM judges?",
    "P20 sandbox": r"sandbox",
    "P22 prompt injection": r"prompt injection",
    "P23 routing": r"\brout(ing|er)\b|cascade",
    "P25 RL": r"reinforcement learning|\bRL\b|GRPO|PPO",
    "P27 cross-repo": r"multi-repo|multi-repository|cross-repo|cross-repository|polyrepo|microservices?",
    "P31 SWE-bench": r"SWE-bench",
    "P32 industrial/field": r"industrial|in production|field study|deployed at|enterprise",
    "lang: Python": r"\bPython\b",
    "lang: Java": r"\bJava\b",
    "domain: healthcare": r"health ?care|clinical|medical|HIPAA",
}


def cmd_landscape(args: argparse.Namespace) -> None:
    papers = [p for p in load_jsonl(ROOT / "papers.jsonl")
              if any(h["relevance"] > 0 for h in p["topic_hits"].values())]
    months = sorted({p["published"][:7] for p in papers if p["published"] >= "2026-05"})
    by_month = {m: [p for p in papers if p["published"].startswith(m)] for m in months}
    agentic = re.compile(r"\b(coding|software engineering|SWE)\b.{0,30}\bagents?\b|\bagentic\b.{0,30}\b(coding|software)", re.I)
    out = ["# Landscape (abstract-level, all gate-passing harvested papers)", "",
           f"Corpus: {len(papers)} papers, submitted {months[0]}..{months[-1]}. Share of abstracts matching each pattern regex.",
           "Abstract mentions measure attention, not evidence.", "",
           "| Pattern | All | " + " | ".join(months) + " | Coding-agent subset |",
           "| --- | --- | " + " | ".join("---" for _ in months) + " | --- |"]
    coding = [p for p in papers if agentic.search(p["title"] + " " + p["abstract"])]
    for name, rx in LANDSCAPE.items():
        r = re.compile(rx, re.I)
        def share(ps):
            return sum(1 for p in ps if r.search(p["title"] + " " + p["abstract"])) / max(1, len(ps))
        cells = " | ".join(f"{share(by_month[m]):.1%}" for m in months)
        out.append(f"| {name} | {share(papers):.1%} | {cells} | {share(coding):.1%} |")
    out += ["", f"Monthly volume: " + ", ".join(f"{m}: {len(by_month[m])}" for m in months),
            f"Coding-agent subset size: {len(coding)}", ""]
    (ROOT / "landscape.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


def cmd_check(args: argparse.Namespace) -> None:
    known, failed = set(TAXONOMY["patterns"]), 0
    for name in args.files:
        try:
            r = json.loads(Path(name).read_text())
            errs = validate(r, known)
        except (OSError, json.JSONDecodeError) as exc:
            errs = [str(exc)]
        if errs:
            failed += 1
            print(f"INVALID {name}: {'; '.join(errs)}")
        else:
            print(f"ok {name} -> gate={admission(r)} weight={weight(r, admission(r))}")
    sys.exit(1 if failed else 0)


def cmd_query(args: argparse.Namespace) -> None:
    db = sqlite3.connect(ROOT / "kb.sqlite")
    for row in db.execute(args.sql):
        print(" | ".join(str(x) for x in row))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("harvest")
    h.add_argument("--pages", type=int, default=1)
    h.add_argument("--per-page", type=int, default=100)
    h.add_argument("--only", nargs="*")
    h.add_argument("--force", action="store_true")
    sub.add_parser("transform")
    s = sub.add_parser("select")
    s.add_argument("--per-topic", type=int, default=4)
    f = sub.add_parser("fulltext")
    f.add_argument("--force", action="store_true")
    sub.add_parser("resignal")
    b = sub.add_parser("batches")
    b.add_argument("--size", type=int, default=8)
    sub.add_parser("landscape")
    ck = sub.add_parser("check")
    ck.add_argument("files", nargs="+")
    sub.add_parser("load")
    sub.add_parser("report")
    qq = sub.add_parser("query")
    qq.add_argument("sql")
    a = ap.parse_args()
    {"harvest": cmd_harvest, "transform": cmd_transform, "select": cmd_select, "fulltext": cmd_fulltext,
     "resignal": cmd_resignal, "batches": cmd_batches, "landscape": cmd_landscape, "check": cmd_check, "load": cmd_load, "report": cmd_report, "query": cmd_query}[a.cmd](a)


if __name__ == "__main__":
    main()
