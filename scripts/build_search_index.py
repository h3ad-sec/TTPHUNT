#!/usr/bin/env python3
"""
Builds data/search-index.json from data/manifest.json + each technique's full
data/techniques/<ID>.json file.

Why this exists: the app used to fetch every technique's FULL json file on
load just to build a client-side search index (fine at 1 pack, wasteful once
there are several -- each pack drags along every query/procedure/concept
string just so the browser can substring-match it). This script precomputes
that searchable text once, offline, into one small file the app fetches
instead -- no more full-content prefetch at runtime.

Run this after adding or editing a technique pack, before committing:
    python scripts/build_search_index.py

It does not touch manifest.json or the technique files themselves -- it only
reads them and (re)writes data/search-index.json.
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def blob_from_parts(parts):
    return " ".join(str(p) for p in parts if p).lower()


def build_technique_blob(full):
    parts = [full.get("id"), full.get("name"), full.get("overview")]
    for c in full.get("prerequisite_concepts", []):
        parts += [c.get("term"), c.get("explanation")]
    return blob_from_parts(parts)


def build_sub_blob(sub):
    parts = [sub.get("id"), sub.get("name"), sub.get("overview")]
    for c in sub.get("concepts", []):
        parts += [c.get("term"), c.get("explanation")]
    hyp = sub.get("hypothesis")
    if hyp:
        parts += [hyp.get("statement"), hyp.get("rationale")]
    for p in sub.get("procedure_examples", []):
        parts += [p.get("actor"), p.get("activity")]
    for d in sub.get("data_sources", []):
        parts += [d.get("source"), d.get("detail")]
    for q in sub.get("detection_queries", []):
        # Deliberately excludes the raw query text -- it's the single
        # largest contributor to file size and the least useful thing to
        # substring-match against (nobody searches for exact query syntax).
        parts += [q.get("title"), q.get("language"), q.get("description")]
    parts += sub.get("false_positives", [])
    parts += sub.get("response_steps", [])
    for m in sub.get("mitigations", []):
        parts += [m.get("id"), m.get("name"), m.get("detail")]
    for r in sub.get("related", []):
        parts += [r.get("id"), r.get("name"), r.get("relation")]
    return blob_from_parts(parts)


def main():
    manifest = read_json(os.path.join(DATA_DIR, "manifest.json"))
    techniques_out = {}
    subtechniques_out = {}

    for t in manifest["techniques"]:
        full = read_json(os.path.join(DATA_DIR, t["file"]))
        techniques_out[full["id"]] = build_technique_blob(full)
        for sub in full.get("subtechniques", []):
            subtechniques_out[sub["id"]] = build_sub_blob(sub)

    out = {
        "generated": manifest.get("generated"),
        "techniques": techniques_out,
        "subtechniques": subtechniques_out,
    }
    out_path = os.path.join(DATA_DIR, "search-index.json")
    write_json(out_path, out)
    print(f"Wrote {out_path}: {len(techniques_out)} techniques, {len(subtechniques_out)} sub-techniques")


if __name__ == "__main__":
    main()
