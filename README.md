# Ropemother exercises

Hands-on exercises for learning message-based software design with the `ropemother` Python package. The current draft is one scaffolded sequence beginning with the 90-minute CCSC Northwest image-reconstruction exercise, followed by Basic Messaging, TTY Processing, Graph Reachability, and a fuller return to the image application.

The exercise code is intended to run directly from a source checkout. The exercise package itself does not need to be installed before following the instructions. `EXERCISES.md` introduces the minimum working context again where it is needed; this README provides fuller setup and troubleshooting support rather than serving as a prerequisite lesson.

## Setup

Use Python 3.13 or newer.

Check the interpreter used by the `python` command:

```sh
python --version
```

The result must begin with `Python 3.13` or a newer version number. Several exercise modules use syntax that older Python interpreters cannot parse.

Clone the repository and enter its root directory:

```sh
git clone https://github.com/edurange/ropemother-exercises.git
cd ropemother-exercises
```

Install `ropemother` from PyPI:

```sh
python -m pip install ropemother
```

Run the exercise commands from the repository root unless an exercise says otherwise.

The current instructions use POSIX-compatible shell features including `export`, `&`, `jobs`, and `kill`. The supported workshop-platform instructions are still being finalized; use a POSIX-compatible shell when following the current draft.

Some exercises use more than one terminal window or tab. The exercise instructions name terminals by the process or role they contain—for example **Broker**, **Word counter**, **Live display**, **Image application**, or **Image interaction**—rather than by number. If the terminal program supports tab or window titles, using those role names can make long-running processes easier to identify after switching windows. Additional terminals can be opened for editing or other work as useful.

## Editor setup

Any editor that saves ordinary plain-text Python files is sufficient. A terminal editor, a lightweight graphical editor, or a larger IDE can all be used; no editor extension, integrated runner, debugger, or project generator is required.

To keep the editor from changing the exercise environment:

1. Open the repository root as the folder or project, not only one file elsewhere on the system.
2. Save each edited file before running it, preserving its `.py` filename and Python indentation.
3. Run the documented `python` and `python -m ...` commands in a terminal whose current directory is the repository root. The editor's Run or Code Runner action is not a substitute for those commands.
4. If using an editor-integrated terminal, check `pwd` and `python --version` there before beginning. They should identify the same repository and supported interpreter as an external terminal.
5. If an extension selects another interpreter, changes the working directory, or runs a file with different arguments, use an ordinary external terminal for the exercise instead of debugging the editor integration during the session.

A low-feature editor is often easier to diagnose because saving a file and running it remain visibly separate actions. Existing reliable editor configurations do not need to be changed.

## Exercise sequence

The participant instructions are in [EXERCISES.md](EXERCISES.md). For the current draft, begin at the top and follow the sections in order:

1. CCSCNW Image Reconstruction
2. Basic Messaging
3. TTY Processing
4. Graph Reachability
5. Image Reconstruction — Full Self-Paced Path

The CCSCNW exercise is both the conference route and the introduction to the longer sequence. The later Image section assumes the intervening exercises have been completed; do not skip directly to it.

## Project status

The exercises are under active development. Commands and participant-facing material are being rehearsed before the workshop and may still change.

Problems with the exercises can be reported through the [GitHub issue tracker](https://github.com/edurange/ropemother-exercises/issues). Changes to the exercises or supporting code should follow [CONTRIBUTING.md](CONTRIBUTING.md).
