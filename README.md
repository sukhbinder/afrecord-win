# afrecord-win

[![PyPI](https://img.shields.io/pypi/v/afrecord-win.svg)](https://pypi.org/project/afrecord-win/)
[![Changelog](https://img.shields.io/github/v/release/sukhbinder/afrecord-win?include_prereleases&label=changelog)](https://github.com/sukhbinder/afrecord-win/releases)
[![Tests](https://github.com/sukhbinder/afrecord-win/actions/workflows/test.yml/badge.svg)](https://github.com/sukhbinder/afrecord-win/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/sukhbinder/afrecord-win/blob/master/LICENSE)

Record sound in cli in windows with standard python.

## Installation

Install this tool using `pip`:
```bash
pip install afrecord-win
```
## Usage

Record audio from the default microphone:
```bash
afrecord
```

Specify a custom output file:
```bash
afrecord -o my_recording.wav
afrecord --output my_recording.wav
```

For help, run:
```bash
afrecord --help
```

You can also use:
```bash
python -m afrecord --help
```

Press **Enter** or **Ctrl+C** to stop recording.
## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd afrecord-win
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
