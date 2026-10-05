# CCSC Northwest 2026 Tutorial Preparation

This page contains preparation information for *Software That Survives Change: Message-Based Design for Research and Student-Developed Projects*.

The 90-minute conference tutorial uses only [Section I: Introduction: Image Reconstruction](EXERCISES.md#i-introduction-image-reconstruction) of the exercise collection. The remaining sections are follow-up exercises and are not part of the conference session. If you wish to continue with the exercises after the tutorial, we welcome your feedback and input.

During the hands-on activity, partial measurements of a hidden image are combined into a reconstruction that changes as new information arrives. Participants will see several independently running parts of the application contribute to that work, use results produced earlier, and continue operating while the code of one component is changed and restarted. The activity provides concrete examples of how message boundaries allow parts of a program to cooperate without requiring them to share the same implementation or lifetime.

A laptop is not required to attend or follow the tutorial. Participants who would like to work through the hands-on activity during the session should bring a laptop and prepare it beforehand.

Comfort reading basic Python is the only programming prerequisite. The tutorial introduces the messaging and image-reconstruction ideas needed for the activity.

## Prepare to Code Along

Hands-on participants will need:

- Python 3.13 or newer;
- a downloaded or cloned copy of this exercise repository;
- a text editor; and
- a terminal with a POSIX-style shell such as `bash` or `zsh`; Windows participants should use WSL.

No account setup or registration is required.

If Git is already installed and you are comfortable using it, clone the repository:

```sh
git clone https://github.com/edurange/ropemother-exercises.git
cd ropemother-exercises
```

If you do not have Git available or prefer not to use it, open the repository on GitHub, choose **Code > Download ZIP**, and extract the ZIP.

After either download route, open a terminal in the top-level repository directory: the directory that contains `EXERCISES.md`, `README.md`, and `pyproject.toml`. Unless an instruction says otherwise, keep your terminal in this directory while working through the exercises.

Check whether `python` runs Python 3.13 or newer:

```sh
python --version
```

If that command is unavailable or reports an older version, try:

```sh
python3 --version
```

Some systems install individual Python versions under commands such as `python3.13` or `python3.14`. If necessary, try the command for the version you installed.

Create a virtual environment using whichever command reported Python 3.13 or newer. For example, if `python` worked:

```sh
python -m venv .venv
```

If `python3` worked instead:

```sh
python3 -m venv .venv
```

A versioned command works the same way. For example:

```sh
python3.14 -m venv .venv
```

Activate the environment:

```sh
source .venv/bin/activate
```

Once the virtual environment is active in a terminal, `python` runs the Python version used to create that environment. The remaining tutorial instructions therefore use `python`.

Check the version once more:

```sh
python --version
```

It should report Python 3.13 or newer.

Install `ropemother`:

```sh
python -m pip install --pre ropemother
```

Some WSL networking configurations can prevent DNS resolution inside WSL even when Windows can reach the same sites. This is a WSL networking issue rather than a problem with `ropemother` or these exercises. If PyPI or another site cannot be reached or resolved, see [WSL Network Troubleshooting](README.md#wsl-network-troubleshooting) in the [README](README.md).

Confirm that `ropemother` is available:

```sh
python -c "import ropemother; print(ropemother.__version__)"
```

The command should print a version number without an error or traceback.

The exercise code runs directly from the repository and does not need to be installed.

The hands-on activity uses more than one terminal. Open each new terminal in the same top-level repository directory and activate the environment:

```sh
source .venv/bin/activate
```

The virtual environment and installed `ropemother` package remain inside `.venv`. Deleting the repository directory after the tutorial removes the exercise files and environment together; no separate uninstall is needed.

Please check this page again shortly before the conference in case the preparation instructions have been updated.