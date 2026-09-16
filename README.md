# Ropemother exercises

Hands-on exercises for learning message-based software design with the `ropemother` Python package.

The participant instructions are in [EXERCISES.md](EXERCISES.md). Run the exercise commands from a copy of this repository; the exercise package itself does not need to be installed.

## Setup

Use Python 3.13 or newer. These instructions assume macOS, Linux, or WSL on Windows and a POSIX-style shell such as `bash` or `zsh`.

Clone the repository and enter its top-level directory:

```sh
git clone https://github.com/edurange/ropemother-exercises.git
cd ropemother-exercises
```

If you download the repository as a ZIP instead, extract it and open a terminal in the extracted `ropemother-exercises` directory before continuing.

Check the interpreter used by the `python` command:

```sh
python --version
```

Create a virtual environment inside the repository and activate it:

```sh
python -m venv .venv
source .venv/bin/activate
```

Install the current developer release of `ropemother` from PyPI:

```sh
pip install --pre ropemother
```

Confirm that the activated environment can import it:

```sh
python -c "import ropemother; print(ropemother.__version__)"
```

You will also need a text editor for the code-editing steps. Run the documented commands from the repository root unless an exercise says otherwise.

The exercises use more than one terminal. In each new terminal, return to the repository root and run `source .venv/bin/activate` before beginning. The `ropemother_exercises` package runs directly from this repository and does not need to be installed.

The virtual environment and its installed copy of `ropemother` remain inside `.venv`. When finished with the exercises, deleting the repository directory removes the exercise files and environment together; no separate uninstall is needed.

## Project status

The exercises are under active development and may change as the materials are revised.

Problems with the exercises can be reported through the [GitHub issue tracker](https://github.com/edurange/ropemother-exercises/issues). Changes to the exercises or supporting code should follow [CONTRIBUTING.md](CONTRIBUTING.md).
