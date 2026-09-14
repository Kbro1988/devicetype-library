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

# Custom device-type YAML conventions

On top of the repo-native structural conventions (2-space indent, sequences indented under their key,
`console-ports` → `interfaces` → `power-ports` → `power-outlets` ordering, types drawn from the enums in
`schema/generated_schema.json`), custom device types on `custom` follow these field patterns:

- `weight_unit: lb` — pounds, not kilograms. Prefer the manufacturer's native lb spec value over a
  kg→lb conversion when the source documentation states it directly.
- `comments:` — a single markdown link to the official data sheet / product page:
  `'[Data Sheet](<url>)'`
- `description:` — `'<Device type> | <VA>/<W> | <voltage>'`, e.g. `'UPS | 5000VA/4000W | 208V'`

# Researching & validating a new device type

When building a device type from manufacturer documentation (as opposed to a user-supplied example):

- Pull specs from the manufacturer's official installer/user guide or spec sheet, not reseller listings
  alone — resellers occasionally disagree with each other (e.g. weight/voltage typos) or omit connector
  detail. Cross-check anything a reseller-only source claims against the official PDF where possible.
- If the official manual is only available as PDF and `pdftotext`/`poppler-utils` aren't installed (no
  `sudo` in this environment), extract text with a throwaway venv: `python3 -m venv /tmp/x/venv &&
  /tmp/x/venv/bin/pip install pypdf`, then `PdfReader(...).pages[i].extract_text()`. Clean up the temp
  dir when done.
- Some products (UPS units especially) ship with a swappable/optional power-distribution accessory
  (e.g. Vertiv's PD2-xxx PODs) rather than one fixed set of outlets — don't assume the first
  configuration found is "the" standard. Check whether the documentation calls out a factory-default,
  and if it genuinely doesn't (multiple options, none marked default), pick the most useful
  configuration for tracking real power connections, note which one was chosen, and flag the assumption
  to the user rather than silently picking one — a config choice that changes the input connector or
  outlet set is a meaningfully different device, not a cosmetic detail.
- Before considering a new file done, validate it locally rather than relying on CI:
  `jsonschema` (`Draft202012Validator`) against `schema/devicetype.json` with `schema/generated_schema.json`,
  `schema/reusable.json`, and `schema/components.json` registered under their `urn:devicetype-library:*`
  ids, plus `yamllint -c .yamllint.yaml`. Both are installable in a throwaway venv the same way as above.

# Rules for Claude

- Never push to `upstream` (its push URL is intentionally disabled).
- Never open a PR from `custom` back to `netbox-community/devicetype-library` unless explicitly asked —
  this branch's content is not meant to be merged upstream.
- Keep `master` free of custom content; all personal additions belong on `custom` (or branches cut from it).
- When syncing, prefer rebase (`custom` onto `master`) over merge to keep history linear, unless told
  otherwise.
