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
  type. Card model-types: `IS-WEBCARD` / `IS-UNITY-DP` (GXT3 and GXT4 — confirmed via their manuals;
  RDU101/RDU120 are **not** compatible with GXT3/GXT4) and `RDU101` / `RDU120` (GXT5, GXT5LI, GXT5 MV
  — both fit the same slot, RDU120 is the newer/gigabit card, neither is tied to a specific chassis
  generation).
- **POD slot** (5000-6000VA-class GXT4/GXT5 MV units only): `module-bays: [{name: Power Distribution
  Box, position: Power Distribution Box}]` on the device type; the chassis's own fixed components
  (e.g. the External Battery Cabinet connector) stay directly on the device type since they aren't
  part of the swappable box. POD model-types: `PD2-HDWR-MBS`/`PD2-001`-`PD2-007` (GXT4-5000/6000RT208)
  and `PD5-UL6HDWR-MBS`/`PD5-001`-`PD5-006` (GXT5-5000/6000MVRT4UXLN) — all documented options built
  as module-types, not just the ones currently in use, so any physically-installed POD can be
  selected later.
- Module-type component names follow the repo's existing UPS-network-card convention (see
  `module-types/APC/AP9631.yaml`, `module-types/CyberPower/RMCARD400.yaml`): suffix each name with
  `[{module}]`, e.g. `Network [{module}]`, `Output 1 [{module}]`.
- POD module-type `description` follows its own summary pattern (network cards keep plain free-text
  descriptions — this pattern is PD2-xxx/PD5-xxx only):
  `'UPS <GXT4|GXT5> | POD | In: <type> (x<qty>) | Out: <type> (x<qty>), <type> (x<qty>), ...'`
  e.g. `'UPS GXT4 | POD | In: L14-30P (x1) | Out: 5-20R (x4), L14-30R (x1), L6-30R (x1)'`. For the
  hardwired PODs (`PD2-HDWR-MBS`, `PD5-UL6HDWR-MBS`) both sides read `In: Hardwired | Out: Hardwired`.
  Family is `GXT4` for `PD2-*` (fits GXT4-5000/6000RT208), `GXT5` for `PD5-*` (fits GXT5-5000/6000MVRT4UXLN).
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

- Pull specs from the manufacturer's official installer/user guide or spec sheet, not reseller listings
  alone — resellers occasionally disagree with each other (e.g. weight/voltage typos) or omit connector
  detail. Cross-check anything a reseller-only source claims against the official PDF where possible.
- If the official manual is only available as PDF and `pdftotext`/`poppler-utils` aren't installed (no
  `sudo` in this environment), extract text with a throwaway venv: `python3 -m venv /tmp/x/venv &&
  /tmp/x/venv/bin/pip install pypdf`, then `PdfReader(...).pages[i].extract_text()`. Clean up the temp
  dir when done.
- Some products (UPS units especially) ship with a swappable/optional power-distribution accessory
  (e.g. Vertiv's PD2-xxx/PD5-xxx PODs) or an optional network card (IntelliSlot) rather than one fixed
  set of components — don't hardcode any single option onto the device type or guess which one a real
  unit has installed. Model these as a `module-bay` and build every documented option as its own
  module-type instead, per **Module bays instead of hardcoded cards/PODs** above.
- Before considering a new file done, validate it locally rather than relying on CI:
  `jsonschema` (`Draft202012Validator`) against `schema/devicetype.json` with `schema/generated_schema.json`,
  `schema/reusable.json`, and `schema/components.json` registered under their `urn:devicetype-library:*`
  ids, plus `yamllint -c .yamllint.yaml`. Both are installable in a throwaway venv the same way as above.

# Rules for Copilot

- Never push to `upstream` (its push URL is intentionally disabled).
- Never open a PR from `custom` back to `netbox-community/devicetype-library` unless explicitly asked —
  this branch's content is not meant to be merged upstream.
- Keep `master` free of custom content; all personal additions belong on `custom` (or branches cut from it).
- When syncing, prefer rebase (`custom` onto `master`) over merge to keep history linear, unless told
  otherwise.
