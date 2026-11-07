#!/usr/bin/env python3
"""Merge the illustrative model and the sourced facts into model/site_data.json (the only data the page reads).

    python3 -I model/lbo_model.py && python3 -I model/build_data.py

- model/lbo_model.json: illustrative LBO outputs (stack, sens, scenarios, qoe, day1). Always called illustrative.
- model/facts_data.json: sourced facts the figures show (timeline, transition, sentiment, hero tiles, deal sizes).
  Every entry carries a "source" key that must exist in model/sources.json, so no figure number is unsourced.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
model = json.loads((HERE / "lbo_model.json").read_text())
facts_path = HERE / "facts_data.json"
facts = json.loads(facts_path.read_text()) if facts_path.exists() else {}
sources = json.loads((HERE / "sources.json").read_text())
ids = {i["id"] for g in sources["groups"] for i in g["items"]}


def walk(o, where=""):
    """Every dict with a 'source' key must point at a known source id (a list of ids is fine too)."""
    bad = []
    if isinstance(o, dict):
        if "source" in o:
            for s in (o["source"] if isinstance(o["source"], list) else [o["source"]]):
                if s not in ids:
                    bad.append(f"{where}: unknown source id '{s}'")
        for k, v in o.items():
            bad += walk(v, f"{where}.{k}" if where else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            bad += walk(v, f"{where}[{i}]")
    return bad


problems = walk(facts)
if problems:
    sys.exit("build_data: " + "\n  ".join(problems))
clash = set(model) & set(facts)
if clash:
    sys.exit(f"build_data: keys in both lbo_model.json and facts_data.json: {sorted(clash)}")
site = {**model, **facts, "as_of": "7 November 2026"}
(HERE / "site_data.json").write_text(json.dumps(site, indent=1))
print(f"build_data: wrote model/site_data.json ({len(site)} top-level keys; facts: {sorted(facts) or 'none yet'})")
