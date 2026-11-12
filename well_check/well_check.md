# WELL mechanical checker

`well_check/well_check.py` is the project's single standard entry point for deterministic mechanical checking of a WELL-governed formal Software Design Description (SDD), including an artifact serving that same formal SDD role under another filename. Running the checker on a non-SDD document does not make that document WELL-governed.

## Runtime requirement

The checker requires only **Python 3.9+ and the Python standard library**. It has no third-party runtime dependency and requires no package installation, virtual environment, network access, Markdown parser package, or parser plugin.

The supported portability check is therefore also valid with Python site-packages disabled:

    python3 -S well_check/well_check.py path/to/document.md

Normal use is simply:

    python3 well_check/well_check.py path/to/document.md

Run the focused tests from the WELL project root with the standard library test runner:

    python3 -S -m unittest tests.well_check.test_well_check tests.well_check.test_stdlib_runtime

`well_check/requirements.txt` intentionally contains no installable requirements; it exists only as an explicit compatibility statement for tooling that expects a requirements file.

## Output contract

The checker writes a canonical JSON receipt to standard output and a concise diagnostic for every violation to standard error. Its status is `PASS`, `FAIL`, or `REVIEW`: `REVIEW` is a deterministic unresolved structural classification, not semantic acceptance. Exit status is zero only for `PASS`, one for `FAIL`, and two for `REVIEW`.

The checker implements only mechanically applicable WELL rules. `WELL-S001` requires the literal lower-case word `because` in each structurally classified prose sentence. `WELL-N001` validates canonical definition names, `WELL-N002` rejects duplicate canonical definitions, and `WELL-N003` rejects non-exact references to recognized canonical definitions. A backticked identifier is not a canonical reference merely because it resembles a lowercase kebab-case name; a definition in the same artifact establishes the mechanically recognizable canonical name. Structural syntax excluded by WELL is listed in `exemptions`; a construct the checker cannot classify is a fail-closed `WELL-U001` `REVIEW` result requiring manual review. A known mechanical violation takes precedence over `REVIEW` and returns `FAIL`.

WELL names block formulas but does not define a machine grammar for them. A paragraph delimited by standalone `$$` markers is therefore reported as the manual-review `possible-block-formula` case, rather than accepted as formula syntax or evaluated as prose. This sentinel does not define a formula grammar or change WELL's mechanical PASS/FAIL scope.

## Native parser boundary

The checker contains one small deterministic parser/classifier implemented directly with Python standard-library string and regular-expression operations. It recognizes only the Markdown structures that WELL mechanically needs: ATX headings, document-start front matter delimiters, fenced and indented code, pipe tables, thematic breaks, list items, blockquotes, simple inline-code spans, bare identifiers, and the explicit unresolved cases defined by WELL.

The parser is deliberately not a general Markdown renderer or semantic Markdown implementation. Unsupported or ambiguous structure must fail closed through the existing WELL `REVIEW` boundary rather than acquire meaning from an unavailable external parser.

`RUNTIME_REQUIREMENT` in `well_check.py` documents the executable requirement in the script itself, and the regression suite executes the checker with `python -S` so accidental third-party imports fail qualification.
