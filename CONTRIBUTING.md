# Contributing

This repository is maintained primarily for eduRange teaching and workshop use. If you find a problem with an exercise, please start by opening an issue. Please discuss substantial changes before opening a pull request; the exercises and supporting code are still changing, and review capacity is limited.

Changes to the `ropemother` library itself belong in its repository:

<https://github.com/edurange/ropemother>

## Before submitting Python changes

The project uses **Black** for formatting and **Pylint** for static analysis. Their shared configuration is in `pyproject.toml`; Black is configured for a 79-character line length and Python 3.13.

Install the development dependencies with:

```sh
python -m pip install -e '.[dev]'
```

Format and check the Python files you changed:

```sh
python -m black path/to/changed_file.py
python -m pylint path/to/changed_file.py
```

New changes should not introduce new Pylint findings in the code being changed.

A fuller automated test suite and CI/CD workflow are still in development. Until those checks are in place, run the affected exercise path or the smallest relevant runnable program from the repository root.

## Exercise changes

Participant instructions and runnable code should agree. When an exercise asks participants to create or substantially edit a file, keep an appropriate completed reference under `_targets/` synchronized with the participant path.

Participant-facing exercise code should use ordinary public `ropemother` interfaces unless an exercise is specifically teaching a public extension point. If an exercise seems to require bus internals or a workaround for a missing public interface, that may need discussion in the exercise or the design of `ropemother` before the workaround is added.

## Reporting exercise problems

Please include enough information to reproduce the point where the instructions and running program diverged:

- exercise section and step;
- command or code that was run;
- output or error that appeared;
- what the instructions led you to expect;
- Python version;
- operating system and shell when relevant.

Issues may be filed at <https://github.com/edurange/ropemother-exercises/issues>.

## License

By submitting a contribution to this repository, you agree that it may be distributed under the MIT License used by this project.
