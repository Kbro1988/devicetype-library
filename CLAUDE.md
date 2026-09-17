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
- `is_full_depth: true` on every UPS model, regardless of measured chassis depth.

# Module bays instead of hardcoded cards/PODs

Vertiv UPS units (and similar gear) take optional/swappable accessories in a physical slot — a
network management card in the IntelliSlot bay, or (on the 5000-6000VA-class GXT4/GXT5 MV models) a
removable power-distribution box (POD) that determines the actual input connector and output
receptacles. Model these as `module-bays` on the device type, not as hardcoded `interfaces` /
`power-ports` / `power-outlets` — the actual components belong on separate module-types under
`module-types/Vertiv/`, so a real device can have whichever card/POD it actually has installed
selected in NetBox, and the UPS device type itself doesn't force one specific assumption.

- **Network card slot**: `module-bays: [{name: IntelliSlot, position: IntelliSlot}]` on the device
  type. Card model-types: `IS-WEBCARD` / `IS-UNITY-DP` / `IS-RELAY` / `IS-485` / `IS-MULTIPORT` (GXT3
  and GXT4 — confirmed via their manuals; RDU101/RDU120 are **not** compatible with GXT3/GXT4) and
  `RDU101` / `RDU120` (GXT5, GXT5LI, GXT5 MV — both fit the same slot, RDU120 is the newer/gigabit
  card, neither is tied to a specific chassis generation). The GXT3 5000-10,000VA line specifically
  uses an even older card set (`IS-RELAY`, `IS-485`, `IS-MULTIPORT`, plus `IS-WEBCARD` under the
  manual's "SNMP Card" name) — don't assume a card family from a smaller/newer sibling model applies
  without checking that exact chassis's own manual.
- IntelliSlot card module-type `description` follows a fixed pattern (screenshot-confirmed by the user):
  `'UPS | IntelliSlot | <Card Name> - <Protocol list> and Web Mgmt.'`, e.g.
  `'UPS | IntelliSlot | Unity Card - SNMP/BACnet/Modbus, RS-485 and Web Mgmt.'`. Card name is the
  product's natural short name (`Web Card` for IS-WEBCARD, `RDU101` for RDU101 — kept as-is when the
  model number already reads as a name). For cards with no IP/web capability at all (`IS-RELAY`,
  `IS-485`, `IS-MULTIPORT` — dry contacts / RS-485 / multiplexed ports only, no SNMP or web UI), drop
  the "and Web Mgmt." suffix rather than claim a capability that doesn't exist, e.g.
  `'UPS | IntelliSlot | Relay Card - Dry-Contact Relay Outputs'`.
- **POD slot** (5000-6000VA-class GXT4/GXT5 MV units only): `module-bays: [{name: Power Distribution
  Box, position: Power Distribution Box}]` on the device type; the chassis's own fixed components
  (e.g. the External Battery Cabinet connector) stay directly on the device type since they aren't
  part of the swappable box. POD model-types: `PD2-HDWR`/`PD2-HDWR-MBS`/`PD2-001`-`PD2-007`
  (GXT3/GXT4-5000/6000RT208 — see the family-label note below) and `PD5-UL6HDWR-MBS`/`PD5-001`-
  `PD5-006` (GXT5-5000/6000MVRT4UXLN) — all documented options built as module-types, not just the
  ones currently in use, so any physically-installed POD can be selected later.
- Module-type component names follow the repo's existing UPS-network-card convention (see
  `module-types/APC/AP9631.yaml`, `module-types/CyberPower/RMCARD400.yaml`): suffix each name with
  `[{module}]`, e.g. `Network [{module}]`, `Output 1 [{module}]`.
- POD module-type `description` follows its own summary pattern (distinct from the IntelliSlot-card
  pattern above — this one is PD2-xxx/PD5-xxx only):
  `'UPS <family> | POD | In: <type> (x<qty>) | Out: <type> (x<qty>), <type> (x<qty>), ...'`
  e.g. `'UPS GXT4 | POD | In: L14-30P (x1) | Out: 5-20R (x4), L14-30R (x1), L6-30R (x1)'`. For the
  hardwired PODs (`PD2-HDWR-MBS`, `PD5-UL6HDWR-MBS`) both sides read `In: Hardwired | Out: Hardwired`.
  Family is `GXT4` for `PD2-*` (fits GXT4-5000/6000RT208), `GXT5` for `PD5-*` (fits GXT5-5000/6000MVRT4UXLN)
  — except `PD2-HDWR-MBS`/`PD2-001`-`PD2-006`, confirmed via the GXT3 5000-10000VA manual's own power-
  distribution table to be the identical shared part across both generations, so those use
  `GXT3/GXT4` instead. `PD2-007` has no GXT3-manual confirmation, so it stays `GXT4`-only — don't
  widen a family label without a source actually naming the older line too.
- POD module-types intentionally omit `maximum_draw` on their power-port — the same POD part fits
  multiple UPS wattages (e.g. PD2-003 fits both the 5000 and 6000VA hosts), so a host-specific draw
  value on the shared module would be misleading.
- **What does *not* become a module bay**: fixed, non-removable chassis ports — USB, RS-232, RS-485,
  etc. that are soldered to the UPS main board. Every manual's rear-panel diagram lists these
  alongside genuinely fixed features (cooling fan, input breaker, EBC connector), never as an item on
  the swappable card or POD options list — check that before assuming a port belongs in a module. If
  there's no alternate part number you could install in its place, it stays as a plain component
  (`console-ports`/`interfaces`) directly on the device type.
- **console-port vs. interface for serial/data ports**: a port used for CLI/terminal access
  (RS-232, or USB used the same way) is a `console-port`. A port that carries a data/BMS protocol
  instead of a CLI session — RS-485 for BACnet MSTP/Modbus RTU, a Liebert SN/Geist sensor-network
  port — is an `interface` with `type: other`, matching this repo's existing convention for such
  ports (see `module-types/APC/AP9631.yaml`'s "Universal I/O" ports). A USB port whose job is
  firmware/config transfer via flash drive (not a terminal session) is still modeled as a
  `console-port`, per existing repo precedent (`module-types/APC/AP9640.yaml`), even though its
  function isn't literally a console — there's no more fitting component type in the schema.

# Researching & validating a new device type

When building a device type from manufacturer documentation (as opposed to a user-supplied example):

- **Confirm the model actually exists before building anything.** Kevin sources model numbers from a
  personal spreadsheet that can contain typos — never assume a given string is correct just because
  search results mention something similar. Check that the exact string appears verbatim in an
  official source (a manufacturer's own "available models" table in a manual, or its product catalog),
  not just that reseller listings echo it. If it doesn't match anything exactly, say so and show the
  closest real match rather than silently building the closest-looking product — this is exactly how
  `GXT5LI-2000LVRT2UX` (missing a trailing "L") got caught before anything was built.
- Pull specs from the manufacturer's official installer/user guide or spec sheet, not reseller listings
  alone — resellers occasionally disagree with each other (e.g. weight/voltage typos) or omit connector
  detail. Cross-check anything a reseller-only source claims against the official PDF where possible.
  Watch for aggregated/AI-summarized search results specifically: a number that's suspiciously close to
  the arithmetic midpoint of two other real values in the same series (e.g. a claimed weight landing
  almost exactly between the row above and below it in a spec table) is a strong signal the summarizer
  interpolated rather than read an actual cell — verify against the primary document directly instead
  of trusting the summary.
- When a manual's own multi-column comparison table conflicts with that model's dedicated product page
  or an independent listing, trust the dedicated page — multi-column PDF tables have repeatedly
  extracted wrong (values shifted or dropped between columns) across this project, while single-model
  pages have been reliable. Cross-check at least one independent source before treating either as final.
- If the official manual is only available as PDF and `pdftotext`/`poppler-utils` aren't installed (no
  `sudo` in this environment), extract text with a throwaway venv: `python3 -m venv /tmp/x/venv &&
  /tmp/x/venv/bin/pip install pypdf`, then `PdfReader(...).pages[i].extract_text()`. Clean up the temp
  dir when done.
- Some products (UPS units especially) ship with a swappable/optional power-distribution accessory
  (e.g. Vertiv's PD2-xxx/PD5-xxx PODs) or an optional network card (IntelliSlot) rather than one fixed
  set of components — don't hardcode any single option onto the device type or guess which one a real
  unit has installed. Model these as a `module-bay` and build every documented option as its own
  module-type instead, per **Module bays instead of hardcoded cards/PODs** above.
- Before considering a new file done, validate it locally rather than relying on CI.
  - **`pytest tests/definitions_test.py -k "..."` silently under-validates uncommitted files — do not
    trust a passing run at face value for a file that isn't committed yet.** Its file discovery is
    git-diff-based (`upstream/master` vs `HEAD`, unioned with `index.diff("HEAD")`), and a brand-new
    file that's only staged (`git add`, not committed) shows up as a spurious "delete" in that diff math
    and gets filtered out — the run reports "N passed" with N files silently missing, no error, no
    warning. This isn't hypothetical: it happened in this project (`GXT4-700RT120.yaml` reported as
    validated when 0 tests had actually run for it). Only genuinely-committed files are reliably
    discovered this way.
  - **For anything not yet committed, validate directly instead** — load schemas with
    `json.loads(..., parse_float=decimal.Decimal)`, YAML with `tests.yaml_loader.DecimalSafeLoader`, and
    run `Draft202012Validator(schema, registry=registry).iter_errors(data)` yourself against the specific
    file paths (don't rely on glob/diff discovery). This is what `tests/definitions_test.py` does
    internally, minus the git-diff file-selection step, so it's just as authoritative and Decimal-safe
    (parsing both the schema *and* the instance data as `Decimal` avoids the binary-float `multipleOf`
    false-positive a naive `yaml.safe_load` + plain-float check can hit — e.g. `5.1` failing a naive
    check even though it's a legitimate weight). Needs `pip install -r requirements.txt` in the
    throwaway venv (for `jsonschema`, `PyYAML`, `referencing`) plus `yamllint -c .yamllint.yaml`.
  - Run the real `pytest -k` suite too as a secondary confirmation once files are committed (or to sanity
    check files that already were committed in an earlier turn) — `DTL_USE_LOCAL_KNOWN_SLUGS=1` avoids a
    network fetch of upstream's known-slugs list.

# Rules for Claude

- Never push to `upstream` (its push URL is intentionally disabled).
- Never open a PR from `custom` back to `netbox-community/devicetype-library` unless explicitly asked —
  this branch's content is not meant to be merged upstream.
- Keep `master` free of custom content; all personal additions belong on `custom` (or branches cut from it).
- When syncing, prefer rebase (`custom` onto `master`) over merge to keep history linear, unless told
  otherwise.
