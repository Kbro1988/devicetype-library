# Repo purpose

This is a fork of [netbox-community/devicetype-library](https://github.com/netbox-community/devicetype-library),
a community-maintained catalog of NetBox device-type YAML definitions (`device-types/`, `module-types/`,
`rack-types/`, `elevation-images/`), validated against JSON schemas in `schema/`.

This fork exists to hold **personal/proprietary device type definitions specific to Kevin's own NetBox
instance** that are not intended to be contributed upstream. It is not a staging area for upstream PRs.

# Remote & branch layout

- `origin` — `git@github.com:Kbro1988/devicetype-library.git` (Kevin's fork; push target)
- `upstream` — `https://github.com/netbox-community/devicetype-library.git` (community repo; pull-only,
  push is disabled locally via `set-url --push upstream DISABLE`)
- `master` — tracks `origin/master`, kept as an exact mirror of `upstream/master`. **Never commit custom
  device types here.** Its only job is to fast-forward cleanly from upstream.
- `custom` — tracks `origin/custom`, branched off `master`. **All personal device-type work happens here.**
  Rebased onto `master` periodically to pick up new upstream device types.

# Workflow

Sync `master` with upstream:

```bash
git checkout master
git pull upstream master
git push origin master
```

Bring personal work up to date with the latest upstream data:

```bash
git checkout custom
git rebase master
git push origin custom --force-with-lease
```

Day-to-day device-type work happens on `custom`: add/edit YAML files under `device-types/<Manufacturer>/`,
follow the same field conventions as `CONTRIBUTING.md` (schema validity, correct slug format, etc.) since
the CI validation in this fork still runs the same checks, then commit and `git push origin custom`.

# Rules for Claude

- Never push to `upstream` (its push URL is intentionally disabled).
- Never open a PR from `custom` back to `netbox-community/devicetype-library` unless explicitly asked —
  this branch's content is not meant to be merged upstream.
- Keep `master` free of custom content; all personal additions belong on `custom` (or branches cut from it).
- When syncing, prefer rebase (`custom` onto `master`) over merge to keep history linear, unless told
  otherwise.
