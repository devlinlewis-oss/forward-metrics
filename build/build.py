#!/usr/bin/env python3
"""Validate the forward-metrics definitions and generate the Claude skill + readable doc.

Usage:
    python3 build/build.py           validate, then write dist/
    python3 build/build.py --check   validate only (exit code 1 on errors)
"""
import shutil
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

STATUSES = {"agreed", "confirm"}
METRIC_TYPES = {"count", "ratio", "unavailable"}
UNITS = {"contacts", "percent", "eur", "eur_per_contact"}
METRIC_REQUIRED = ["name", "label", "status", "type", "description", "formula", "unit", "owner"]
DIMENSION_REQUIRED = ["name", "label", "status", "properties", "rule"]
STAGE_REQUIRED = ["id", "label", "lifecycle_value", "entry_date_property", "status"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ordered(folder):
    """Load every YAML file in a folder, keyed by file stem, sorted by its `order` field."""
    items = {p.stem: load(p) for p in folder.glob("*.yml")}
    return dict(sorted(items.items(), key=lambda kv: (kv[1].get("order", 99), kv[0])))


def load_all():
    return {
        "skill": load(ROOT / "skill.yml"),
        "funnel": load(ROOT / "stages" / "funnel.yml"),
        "dimensions": ordered(ROOT / "dimensions"),
        "metrics": ordered(ROOT / "metrics"),
        "rules": sorted(
            (load(p) for p in (ROOT / "rules").glob("*.yml")), key=lambda r: r.get("order", 99)
        ),
        "sources": load(ROOT / "sources.yml")["sources"],
        "glossary": load(ROOT / "glossary.yml")["terms"],
    }


# ---------------------------------------------------------------- validation

def validate(d):
    errors = []
    err = errors.append

    stage_ids = set()
    for s in d["funnel"]["stages"]:
        for k in STAGE_REQUIRED:
            if k not in s:
                err(f"stages/funnel.yml: stage {s.get('id', '?')} missing '{k}'")
        if s.get("id") in stage_ids:
            err(f"stages/funnel.yml: duplicate stage id {s['id']}")
        stage_ids.add(s.get("id"))
        if s.get("status") not in STATUSES:
            err(f"stages/funnel.yml: stage {s.get('id')} has invalid status {s.get('status')!r}")

    for stem, dim in d["dimensions"].items():
        where = f"dimensions/{stem}.yml"
        for k in DIMENSION_REQUIRED:
            if k not in dim:
                err(f"{where}: missing '{k}'")
        if dim.get("name") != stem:
            err(f"{where}: name {dim.get('name')!r} doesn't match file name")
        if dim.get("status") not in STATUSES:
            err(f"{where}: invalid status {dim.get('status')!r}")

    source_ids = {s["id"] for s in d["sources"]}
    benchmark_ids = {
        b["id"] for r in d["rules"] for b in r.get("benchmarks", [])
    }
    metric_names = set(d["metrics"])

    def check_ref(where, side, ref):
        if not isinstance(ref, dict) or len(ref) != 1:
            err(f"{where}: {side} must be one of {{stage: ...}}, {{metric: ...}}, {{expression: ...}}")
            return
        (kind, value), = ref.items()
        if kind == "stage" and value not in stage_ids:
            err(f"{where}: {side} refers to unknown stage {value!r}")
        elif kind == "metric" and value not in metric_names:
            err(f"{where}: {side} refers to unknown metric {value!r}")
        elif kind not in {"stage", "metric", "expression"}:
            err(f"{where}: {side} has unknown reference type {kind!r}")

    for stem, m in d["metrics"].items():
        where = f"metrics/{stem}.yml"
        for k in METRIC_REQUIRED:
            if k not in m:
                err(f"{where}: missing '{k}'")
        if m.get("name") != stem:
            err(f"{where}: name {m.get('name')!r} doesn't match file name")
        if m.get("status") not in STATUSES:
            err(f"{where}: invalid status {m.get('status')!r}")
        if m.get("type") not in METRIC_TYPES:
            err(f"{where}: invalid type {m.get('type')!r}")
        if m.get("unit") not in UNITS:
            err(f"{where}: invalid unit {m.get('unit')!r}")
        if m.get("type") == "ratio":
            for side in ("numerator", "denominator"):
                if side not in m:
                    err(f"{where}: ratio metric missing '{side}'")
                else:
                    check_ref(where, side, m[side])
        for dim in m.get("slice_by", []):
            if dim not in d["dimensions"]:
                err(f"{where}: slice_by refers to unknown dimension {dim!r}")
        if m.get("benchmark") and m["benchmark"] not in benchmark_ids:
            err(f"{where}: unknown benchmark {m['benchmark']!r}")
        if m.get("source") and m["source"] not in source_ids:
            err(f"{where}: unknown source {m['source']!r}")
        owner = m.get("owner", {})
        if not isinstance(owner, dict) or not {"definition", "calculation"} <= set(owner):
            err(f"{where}: owner needs 'definition' and 'calculation'")

    for stem, dim in d["dimensions"].items():
        if dim.get("source") and dim["source"] not in source_ids:
            err(f"dimensions/{stem}.yml: unknown source {dim['source']!r}")

    return errors


# ---------------------------------------------------------------- rendering

def tag(obj):
    return " [confirm]" if obj.get("status") == "confirm" else ""


def cell(text):
    return " ".join(str(text).split()).replace("|", "\\|")


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def render_rule(r):
    lines = [f"## {r['title']}", ""]
    if r.get("benchmarks"):
        for b in r["benchmarks"]:
            text = f"- **{b['label']}:** {cell(b['rule'])}"
            if b.get("markets"):
                text += f" In {' and '.join(b.get('cycles', []))} these are {', '.join(b['markets'])}."
            lines.append(text)
    for i, item in enumerate(r.get("items", []), 1):
        prefix = f"{i}." if r.get("numbered") else "-"
        lines.append(f"{prefix} {cell(item)}")
    return "\n".join(lines)


def render(d):
    s = d["skill"]
    by_id = {r["id"]: r for r in d["rules"]}
    out = [f"# {s['title']}", "", s["intro"].strip(), ""]

    out += [render_rule(by_id["reporting"]), ""]

    out += ["## Dimensions", ""]
    out.append(table(
        ["Concept", "Property", "Rule"],
        [[dim["label"] + tag(dim), ", ".join(dim["properties"]) or "-", dim["rule"]]
         for dim in d["dimensions"].values()],
    ))
    out.append("")
    for dim in d["dimensions"].values():
        if dim.get("values") or dim.get("notes"):
            out += [f"### {dim['label']}{tag(dim)}", ""]
            if dim.get("values"):
                out.append(table(
                    ["Group", "Definition"],
                    [[v.get("label", v["value"]), v["definition"]] for v in dim["values"]],
                ))
                out.append("")
            for n in dim.get("notes", []):
                out.append(f"- {cell(n)}")
            if dim.get("notes"):
                out.append("")

    f = d["funnel"]
    out += ["## Funnel stages", "", cell(f["rule"]), ""]
    out.append(table(
        ["Stage", "Lifecycle value", "Entry date property"],
        [[st["label"] + tag(st), st["lifecycle_value"], st["entry_date_property"]] for st in f["stages"]],
    ))
    out.append("")

    out += ["## Terms", ""]
    for t in d["glossary"]:
        out.append(f"- **{t['term']}:** {cell(t['definition'])}")
    out.append("")

    out += ["## Metrics", ""]
    available = [m for m in d["metrics"].values() if m["type"] != "unavailable"]
    unavailable = [m for m in d["metrics"].values() if m["type"] == "unavailable"]
    for m in available:
        out += [f"### {m['label']}{tag(m)} (`{m['name']}`)", "", cell(m["description"]), ""]
        out.append(f"- **Formula:** {cell(m['formula'])}")
        if m.get("parameter"):
            out.append(f"- **Parameter:** {m['parameter']} (any funnel stage)")
        for k, label in [("time_anchor", "Time anchor"), ("period_rule", "Period")]:
            if m.get(k):
                out.append(f"- **{label}:** {cell(m[k])}")
        for flt in m.get("filters", []):
            out.append(f"- **Filter:** {cell(flt)}")
        out.append(f"- **Unit:** {m['unit']}")
        if m.get("slice_by"):
            out.append(f"- **Slice by:** {', '.join(m['slice_by'])}")
        if m.get("benchmark"):
            out.append(f"- **Benchmark:** {m['benchmark']} (see Benchmarks)")
        for n in m.get("notes", []):
            out.append(f"- {cell(n)}")
        out.append("")

    if unavailable:
        out += ["## Not available yet", "", "Don't estimate these. Say they can't be calculated and why.", ""]
        for m in unavailable:
            out.append(f"- **{m['label']}:** " + " ".join(cell(n) for n in m.get("notes", [])))
        out.append("")

    out += ["## Sources", ""]
    for src in d["sources"]:
        line = f"- **{src['label']}:** {', '.join(src['owns'])}."
        if src.get("notes"):
            line += " " + " ".join(cell(n) for n in src["notes"])
        out.append(line)
    out.append("")

    for r in d["rules"]:
        if r["id"] != "reporting":
            out += [render_rule(r), ""]

    return "\n".join(out).rstrip() + "\n"


def write_dist(d, body):
    s = d["skill"]
    if DIST.exists():
        shutil.rmtree(DIST)
    skill_dir = DIST / s["name"]
    skill_dir.mkdir(parents=True)
    header = "<!-- Generated by build/build.py from the forward-metrics repo. Don't edit by hand. -->\n\n"
    frontmatter = f"---\nname: {s['name']}\ndescription: {cell(s['description'])}\n---\n\n"
    (skill_dir / "SKILL.md").write_text(frontmatter + header + body, encoding="utf-8")
    (DIST / "forward-metric-definitions.md").write_text(header + body, encoding="utf-8")
    with zipfile.ZipFile(DIST / f"{s['name']}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(skill_dir / "SKILL.md", f"{s['name']}/SKILL.md")


def main():
    d = load_all()
    errors = validate(d)
    if errors:
        print(f"{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    n_confirm = sum(
        1 for x in [*d["metrics"].values(), *d["dimensions"].values(), *d["funnel"]["stages"]]
        if x.get("status") == "confirm"
    )
    print(f"OK: {len(d['metrics'])} metrics, {len(d['dimensions'])} dimensions, "
          f"{len(d['funnel']['stages'])} stages, {n_confirm} marked [confirm]")
    if "--check" in sys.argv:
        return
    write_dist(d, render(d))
    print(f"Wrote {DIST.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
