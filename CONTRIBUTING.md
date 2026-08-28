# Contributing

This repository is maintained primarily for eduRange teaching and workshop use. If you find a problem with an exercise, please start by opening an issue. Please discuss changes before opening a pull request; the exercises and supporting code are still changing, and review capacity is limited.

Changes to the `ropemother` library itself belong in its repository:

<https://github.com/edurange/ropemother>

## Reporting exercise problems

Please include enough information to reproduce the point where the instructions and running program diverged:

- exercise section and step;
- command or code that was run;
- output or error that appeared;
- what the instructions led you to expect;
- Python version;
- operating system and shell when relevant.

Issues may be filed at <https://github.com/edurange/ropemother-exercises/issues>.

## Development checks

For an agreed Python code change, install the development dependencies with:

```sh
python -m pip install -e ".[dev]"
```

Format and check changed Python files with Black and Pylint using the configuration in `pyproject.toml`:

```sh
python -m black path/to/changed_file.py
python -m pylint path/to/changed_file.py
```

## License

By submitting a contribution to this repository, you agree that it may be distributed under the MIT License used by this project.
