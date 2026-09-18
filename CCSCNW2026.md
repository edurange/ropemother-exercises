# CCSC Northwest 2026 tutorial preparation

This page contains preparation information for *Software That Survives Change: Message-Based Design for Research and Student-Developed Projects*.

The 90-minute conference tutorial uses only [Section I: Introduction: Image Reconstruction](EXERCISES.md#i-introduction-image-reconstruction) of the exercise collection. The remaining sections are follow-up exercises and are not part of the conference session.

During the hands-on activity, participants run a small image-reconstruction program. They add sensor sources, complete runs and request reports, inspect the same completed work from a separate command, then edit and restart one reporting service without restarting the rest. These steps show how the parts communicate through messages, how one part can change without forcing changes elsewhere, and how earlier messages can be used later.

A laptop is not required to attend or follow the tutorial. Participants who would like to work through the hands-on activity during the session should bring a laptop and prepare it beforehand.

Comfort reading basic Python is the only programming prerequisite. The tutorial introduces the messaging and image-reconstruction ideas needed for the activity.

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