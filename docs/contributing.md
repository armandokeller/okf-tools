# Contributing

Contributions are welcome — bug reports, feature ideas, and pull requests
alike.

- **Found a bug, or have an idea?** [Open an issue](https://github.com/armandokeller/okf-tools/issues/new).
  Include enough to reproduce: Python version, the relevant command or
  snippet, and what you expected vs. what happened.
- **Want to fix it yourself?** Fork the repo, create a branch off `main`,
  make your change, and open a pull request. For anything nontrivial,
  opening an issue first to align on the approach before writing code is
  welcome but not required.

A few guidelines to keep reviews quick and the codebase consistent:

- Keep pull requests focused on one change — smaller PRs get reviewed
  faster than ones that mix unrelated fixes.
- Before opening a PR, run the full check suite:

    ```bash
    uv run pytest
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy src
    ```

- Add or update tests for any behavior change; the wiring tests in
  `tests/test_*_integration.py` are good templates for framework-adapter
  changes.
- Match the existing code style: no comments explaining *what* code
  does (names should already make that clear) — only comment on
  non-obvious *why*.
- Write commit messages and PR descriptions that explain *why*, not just
  *what* changed.
- By submitting a contribution, you agree it's licensed under this
  project's [MIT license](https://github.com/armandokeller/okf-tools/blob/main/LICENSE).
