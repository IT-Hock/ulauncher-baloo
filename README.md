# Baloo ulauncher Extension

<img align="center" src="https://github.com/user-attachments/assets/2332387a-9186-4019-a579-56438811f58a">

This extension allows you to search for files and folders in your system using the Baloo file indexer. It is based on the [Baloo](https://api.kde.org/frameworks/baloo/html/index.html) library, which is the file indexing and search framework for KDE Plasma.


## Running tests

Setup

```sh
git clone https://github.com/Ulauncher/Ulauncher
ULAUNCHER_PTH=$(python -c 'import site; print(site.getsitepackages()[0])')/ulauncher.pth
realpath Ulauncher > $ULAUNCHER_PTH

pip install websocket-client python-Levenshtein
pip install pytest pytest-pep8 freezegun
```

Run tests

```sh
pytest
```