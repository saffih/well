# WELL — Warranted, Explicit, Lean, Linked

WELL is a portable standard for making design documents inspectable, locally warranted, explicit, lean, and linked.

The normative standard is [`well.md`](well.md). The repository also includes the deterministic mechanical checker, its pinned dependencies, and focused tests.

WELL is intentionally independent of any project-specific architecture process, authority chain, review method, implementation workflow, or acceptance gate. Adopting projects decide those separately.

## Quick start

```bash
python3 -m venv well_check/.venv
well_check/.venv/bin/python -m pip install -r well_check/requirements.txt
well_check/.venv/bin/python well_check/well_check.py path/to/document.md
```

Run the focused tests:

```bash
well_check/.venv/bin/python -m unittest tests.well_check.test_well_check
```

The checker returns `PASS`, `FAIL`, or `REVIEW`. Mechanical WELL conformance does not establish semantic design correctness or project acceptance; see the normative standard for the exact boundary.

## Author and license

Original author: Saffi Hartal.

Released under the MIT License. See [`LICENSE`](LICENSE).
