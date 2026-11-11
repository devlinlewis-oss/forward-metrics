# forward-metrics

Forward College's semantic layer: every admissions, marketing, spend and financial aid
metric defined once, as structured files, so every report, dashboard and Claude session
calculates it the same way.

The YAML files in this repo are the source of truth. The Campus Claude skill and the
readable definitions doc are **generated** from them. Don't edit the generated files.

## Layout

```
skill.yml          Skill name, description and opening instructions
stages/            Funnel stages: lifecycle value + entry-date property
dimensions/        What metrics can be sliced by (market, cycle, channel...)
metrics/           One file per metric: formula, filters, time anchor, owner
rules/             Reporting rules, benchmarks, data limits, HubSpot query limits
sources.yml        Which system owns each fact
glossary.yml       Vocabulary and naming rules
build/build.py     Validates everything, then generates dist/
dist/              Generated: skill folder, skill zip, readable doc
OPEN_QUESTIONS.md  Definitions not yet signed off, and known conflicts
```

## Working on it

```bash
pip install pyyaml
python3 build/build.py           # validate + generate dist/
python3 build/build.py --check   # validate only (use before committing)
```

Each definition has a `status`:

- `agreed`: signed off by the Digital Team.
- `confirm`: working definition. Claude states it whenever it uses it.

## Changing a definition

1. Edit or add the YAML file (Claude Code can draft it).
2. Run `python3 build/build.py --check`.
3. Commit with a message that says what changed and why. If someone else needs to agree
   (the metric's definition owner), open a pull request and have them approve it.
4. Run the full build and upload `dist/forward-metric-definitions.zip` to Campus Claude.

## Metric file format

```yaml
name: yield                 # unique id, snake_case, matches the file name
label: Yield
status: agreed              # agreed | confirm
type: ratio                 # count | ratio
description: One plain-English sentence on what it measures.
numerator: {stage: enrolled}        # a stage, or {metric: <name>}
denominator: {stage: admitted}
filters: [Cycle filter on admissions_cycle_year]
time_anchor: Stage entry dates
unit: percent               # contacts | percent | eur | eur_per_contact
period_rule: Complete cycles only
slice_by: [market, cycle]   # names of files in dimensions/
benchmark: all_countries    # a benchmark id in rules/benchmarks.yml
owner:
  definition: unassigned    # who decides what it means
  calculation: Devlin       # who owns how it's computed
notes: [Anything an analyst would otherwise get wrong]
```
