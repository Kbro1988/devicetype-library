---
name: new-device-definition
description: Research and add a NetBox device or module definition using this repository's source, modeling, and validation rules.
---

# Adding a new device definition

Use this skill when creating or substantially updating a file under `device-types/`,
`module-types/`, or `rack-types/`.

## Procedure

1. Work on `custom`, not `master`. Confirm the exact model or part number in an official
   manufacturer manual, product page, or catalog before creating a file. If the exact string
   cannot be confirmed, stop and report the closest documented match instead of silently
   substituting it.
2. Prefer official installer/user guides and spec sheets for weight, dimensions, voltage,
   connectors, airflow, and component names. Cross-check unusual values against an independent
   source. For PDF-only sources without system PDF tools, use a temporary virtualenv with
   `pypdf` and remove it afterward.
3. Separate fixed chassis components from optional/swappable components. Put fixed ports on
   the device; represent replaceable cards, power supplies, PODs, and similar accessories as
   module types connected through `module-bays`.
4. Name the file after the exact model/part number and use a lowercase manufacturer-prefixed
   slug. Follow the schema and `CONTRIBUTING.md`: attributes first, two-space indentation,
   complete interface names, no empty values, and a trailing newline.
5. For an uncommitted file, validate directly because the normal pytest harness discovers
   definitions from git diff and can silently miss a brand-new file:

   ```bash
   make validate-file FILE=device-types/Manufacturer/Model.yaml
   ```

6. Run targeted lint and, after the file is committed or otherwise included in the diff,
   run the targeted pytest check:

   ```bash
   yamllint --config-file .yamllint.yaml --strict device-types/Manufacturer/Model.yaml
   DTL_USE_LOCAL_KNOWN_SLUGS=1 python -m pytest tests/definitions_test.py -k 'Model' -v
   ```

7. For custom Vertiv UPS definitions, also apply the conventions in
   `.github/copilot-instructions.md`: pounds when the source gives pounds, official data-sheet
   links in `comments`, the standard UPS description, `is_full_depth: true`, and module bays
   for IntelliSlot cards and applicable PODs.

## Completion checks

Before reporting completion, confirm the exact source model, schema validation, YAML lint,
filename/slug rules, fixed-versus-modular component placement, and any required module-type
references. Do not edit generated `tests/known-*.json` caches manually.
