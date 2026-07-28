# CLAUDE.md

This repo **is** the `statscan-tables` Claude Code skill — its source of truth, not a consumer
of it. Changes here get distributed two ways:
1. Zipped/cloned into users' `~/.claude/skills/statscan-tables/`
2. Vendored verbatim into `statscan-to-pbc` (its `scripts/vendor_sync.py` pulls `SKILL.md` and
   `references/known-vectors.md` from here — this repo is canonical per `84ec4cf` "mark this
   project as canonical source for vendoring")

**Before editing SKILL.md or references/known-vectors.md:** consider whether the change should
also flow to `statscan-to-pbc`, since that project pulls from here, not the other way around.

## What's actually in the box

- `SKILL.md` — the fetch → clean → transform → verify protocol itself. This is the skill's
  entire behavioral spec; there is no separate "app code."
- `scripts/wds_fetch.py`, `scripts/cube_metadata.py` — stdlib-only Python (3.10+), no
  dependencies to install or manage.
- `references/known-vectors.md` — canonical ledger of verified vectors. Append-only in normal
  use; the skill instructs Claude to write to it during Step 1, not defer it.

## Gotchas specific to this repo

- **Don't add dependencies.** The whole pitch is "nothing to install beyond Python 3.10+." A new
  pip dependency breaks that promise for every downstream install.
- **`known-vectors.md` is canonical here, read-only elsewhere.** If you're tempted to fix a
  vector entry from the `statscan-to-pbc` side, fix it here instead and let vendor_sync pull it.
- **Version bumps matter downstream.** `SKILL.md` frontmatter `version:` and `CHANGELOG.md` are
  what vendoring users reconcile against — bump and log deliberately, not as a drive-by edit.
- **No CI/test runner beyond `scripts/test_wds_fetch.py`.** Run it directly with `python
  scripts/test_wds_fetch.py` after touching `wds_fetch.py`.

## Not applicable here

Standard "large codebase" practices (hierarchical CLAUDE.md, LSP integration, MCP servers,
subagent explore/edit split, monorepo governance) don't apply — single-purpose, single-language,
no build step, no multi-directory structure. Skip them.
