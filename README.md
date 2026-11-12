# WELL — Warranted, Explicit, Lean, Linked

WELL offers **two separate uses**, selected by the document's function rather than its filename.

| Use | File | Intended documents | Checking |
| --- | --- | --- | --- |
| **Formal WELL** | [`well.md`](well.md) | Formal Software Design Descriptions (SDDs), including documents serving that same formal SDD role under another name | Mechanical WELL conformance checker |
| **WELL Idiom** | [`well-idiom.md`](well-idiom.md) | Skills, `AGENTS.md`, definitions, working-design notes, implementation plans, roadmaps, and other non-SDD working documents | No mechanical checker or formal conformance |

Formal WELL makes an SDD's propositions warranted, explicit, lean, and linked. Its checker and focused tests are included in this repository. **Discussing design, having a `.md` extension, living under `design/`, or running the checker does not make a document an SDD.**

WELL Idiom borrows the useful `claim, because reason` writing pattern and meaning-preserving practices without the formal structure, required token, or ceremony of an SDD.

These are distinct scopes, **not two levels of formal WELL compliance**. Neither file depends on project-specific architecture processes, acceptance gates, or private repository conventions.

## Formal SDD checker

Use these commands only when formal WELL conformance is intended; WELL Idiom needs no installation or checker.


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
