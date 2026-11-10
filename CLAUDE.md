# Working in forward-metrics

This repo is Forward College's semantic layer. The YAML files are the source of truth for
how every metric is calculated. `dist/` is generated: never edit it by hand.

## Rules

- One fact, one place. Before adding a definition, search the repo for the concept. If it
  exists, edit that file rather than creating a second one.
- Two legitimate definitions get two names (for example `applicants_submitted` and
  `applicants_eligible`), never one name with two meanings.
- New or changed definitions start as `status: confirm` unless Devlin says they're agreed.
- Never invent a HubSpot property name, lifecycle value or spend source. If unsure, look it
  up with the HubSpot tools or ask, and record what you checked in the file's `notes`.
- Add anything unresolved to OPEN_QUESTIONS.md.
- After any change, run `python build/build.py --check` and fix every error before
  finishing.

## When an analysis session finds a gap

If, during analysis elsewhere, a definition was missing, ambiguous or guessed, propose the
change here: show the YAML diff, say which analysis surfaced it, and wait for Devlin to
approve before committing.
