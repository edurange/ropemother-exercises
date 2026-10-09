# `ropemother-exercises`

Hands-on exercises for learning message-based software design with the `ropemother` Python package.

If you are preparing for the CCSC Northwest 2026 tutorial, see [CCSCNW2026.md](CCSCNW2026.md). The complete participant instructions are in [EXERCISES.md](EXERCISES.md).

## Setup

Use Python 3.13 or newer. These instructions assume macOS, Linux, or WSL on Windows and a POSIX-style shell such as `bash` or `zsh`.

Make a local copy of the repository. If Git is already installed and you are comfortable using it, clone the repository:

```sh
git clone https://github.com/edurange/ropemother-exercises.git
cd ropemother-exercises
```

If you do not use Git, open the repository on GitHub, choose **Code > Download ZIP**, extract the ZIP, and open a terminal in the extracted repository directory.

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
python3.13 -m venv .venv
```

Activate the environment:

```sh
source .venv/bin/activate
```

Once the virtual environment is active in a terminal, `python` runs the Python version used to create that environment. The remaining instructions therefore use `python`.

Check the version once more:

```sh
python --version
```

It should report Python 3.13 or newer.

Install the `ropemother` release used by these exercises:

```sh
python -m pip install --pre ropemother
```

### WSL Network Troubleshooting

Some WSL configurations can have DNS or other networking problems even when Windows itself can reach the Internet. If this happens, commands inside WSL may report name-resolution or connection errors when trying to reach PyPI, GitHub, or other sites.

Microsoft documents several WSL networking and DNS configurations that can cause this problem. Updating WSL may resolve problems that have already been fixed:

```powershell
wsl --update
```

Run that command from Windows PowerShell or Command Prompt, not from the Linux shell. Then close and reopen WSL and try the failed command again.

For additional diagnosis and repair options, see [Microsoft's WSL troubleshooting documentation](https://learn.microsoft.com/windows/wsl/troubleshooting).

If Windows can reach the required sites but WSL still cannot, you can also use the Windows browser to download the files you need.

If you do not have Git available or prefer not to use it, open the repository on GitHub, choose **Code > Download ZIP**, and extract the ZIP.

For `ropemother`, open its [PyPI page](https://pypi.org/project/ropemother/), choose **Download files**, and download the `.whl` file for the current release.

Windows drives are available inside WSL under `/mnt`. For example, if the wheel is in your Windows Downloads folder on the `C:` drive, install it using its WSL path:

```sh
python -m pip install "/mnt/c/Users/<username>/Downloads/<wheel-filename>.whl"
```

Replace `<username>` and `<wheel-filename>` with the names on your system, and adjust the path if you saved the wheel somewhere else.

### Verify Installation

Confirm that `ropemother` is ready:

```sh
python -c "import ropemother; print(ropemother.__version__)"
```

The command should print a version number without an error or traceback.

The `ropemother_exercises` package itself runs directly from this repository and does not need to be installed.

The exercises use more than one terminal. Open each new terminal in the same top-level repository directory and activate the environment:

```sh
source .venv/bin/activate
```

When setup is complete, continue with [EXERCISES.md](EXERCISES.md).

## Project status

The exercises are under active development and may change as the materials are revised.

Problems with the exercises can be reported through the [GitHub issue tracker](https://github.com/edurange/ropemother-exercises/issues). Changes to the exercises or supporting code should follow [CONTRIBUTING.md](CONTRIBUTING.md).
