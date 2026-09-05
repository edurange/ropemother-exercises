# CCSC Northwest 2026 tutorial preparation

This page contains preparation information for *Software That Survives Change: Message-Based Design for Research and Student-Developed Projects*.

A laptop is not required to attend or follow the tutorial. Participants who would like to work through the hands-on exercise during the session should bring a laptop and prepare it beforehand.

Comfort reading basic Python is the only programming prerequisite. The tutorial will introduce the messaging and image-reconstruction ideas used in the exercise.

## Prepare to code along

Hands-on participants will need:

* Python 3.13 or newer
* a downloaded or cloned copy of this exercise repository
* a text editor
* a terminal with a POSIX-style shell, such as `bash` or `zsh`; Windows participants should use WSL

No account setup or registration is required.

Clone the repository and enter its top-level directory:

```sh
git clone https://github.com/edurange/ropemother-exercises.git
cd ropemother-exercises
```

If you prefer not to use Git, download the repository as a ZIP, extract it, and open a terminal in the extracted `ropemother-exercises` directory.

Check your Python version, create a virtual environment inside the repository, activate it, and install the current developer release of `ropemother`:

```sh
python --version
python -m venv .venv
source .venv/bin/activate
pip install --pre ropemother
```

Confirm that the setup is ready:

```sh
python -c "import ropemother; print(ropemother.__version__)"
```

The exercise code runs directly from the repository and does not need to be installed. When the tutorial asks you to open another terminal, return to the repository directory and run `source .venv/bin/activate` in that terminal as well.

The virtual environment and installed `ropemother` package remain inside `.venv`. Deleting the repository directory after the tutorial removes the exercise files and environment together; no separate uninstall is needed.

Please check this page again shortly before the conference in case the preparation instructions have been updated.