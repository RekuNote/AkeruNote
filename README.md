<p align="center">
    <img width="500" heigth="160" src="logo.png">
    </p>
</p>

AkeruNote is a (half broken, probably) Flipnote Hatena server for the Nintendo DSi written for Python 3.12.3. This project allows you to host your own Flipnote Hatena server with enhanced features and customizations.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Features

- Host your own Flipnote Hatena server
- Customizable features and settings
- Support for multiple databases (untested)

## Requirements

- Python 3.6+
- The following Python packages:
  - twisted
  - pillow
  - termcolor
  - colorama
  - pymongo
  - flask

## Installation

### Clone the Repository

First, clone the repository to your local machine:

```sh
git clone https://github.com/yourusername/akerunote.git
cd akerunote
```

### Setting Up the Virtual Environment

It's recommended to use a virtual environment to manage dependencies:

```sh
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Installing Required Packages

Install the required packages using `pip`:

```pip install twisted```<br>
```pip install pillow```<br>
```pip install termcolor```<br>
```pip install colorama```<br>
```pip install pymongo```<br>
```pip install flask```<br>


### Directory Structure

Ensure the directory structure is set up correctly:

```
akerunote/
├── Akeru/
│   ├── HatenaDB/
│   │   └── __init__.py
│   ├── AkeruRoot/
│   │   └── <your_files>
│   └── __init__.py
├── AkeruTools/
│   ├── UGO.py
│   └── __init__.py
├── DB.py
├── hatena.py
├── start.py
├── requirements.txt
└── README.md
```

### Initial Configuration

Before running the server, ensure all configurations are set correctly in the `start.py`, `DB.py`, and `hatena.py` files.

## Usage

To start the AkeruNote server, simply run `start.py`:

```python3 start.py```

This will start the server on the default port (9090). You will most likely need to change this to 8080 for proper use.

## License

AkeruNote is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html). You are free to use, modify, and distribute this software under the terms of the GPLv3.

