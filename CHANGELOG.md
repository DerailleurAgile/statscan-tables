# Changelog

The skill's version lives in SKILL.md frontmatter (`version:`). Bump it and add an entry here
with every change that gets packaged/uploaded — patch for fixes, minor for behavior changes.

## 1.1.0 — 2026-07-07

Alignment with statscan-to-pbc v1.1.0 (the non-PBC lessons from its claude.ai/cloud shakedown):

- Cloud-session note in Step 2: `www150.statcan.gc.ca` must be in the environment's custom
  network allowlist or all WDS calls fail; clipboard copy is silently skipped in cloud sessions.
- Output files go to the session temp/scratchpad directory by default, into the project only on
  request.
- `version:` in SKILL.md frontmatter; this changelog; `dist/` zip packaging for claude.ai upload.

(The frontmatter description was already within claude.ai's 1024-character upload limit, and
tab-delimited output was already the default here — no changes needed for those.)

## 1.0.0 — 2026-07-06

- Initial packaged skill: WDS fetch/verify pipeline (stdlib-only scripts), cached cube metadata,
  known-vectors reference, clipboard auto-copy.
