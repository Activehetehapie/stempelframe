# Introduction

Welcome to the Vrolijk repository

# Developing app

In this app API calls to nuclei are made. These require a user and password. These can be added when starting the app:

```
./viktor-cli start vrolijk --env VIKTOR_APP_SECRET="user|password"
```
This app makes use of code quality tools. These tools are isolated in a seperate requirements file (`dev-requirements.txt`). The following sections helps you with the setup and using these tools.

## Creating a virtual enviroment

To create a venv on Linux:

```
python3 -m venv .env
```

Activate the virtual environment:
```
source ./.env/bin/activate
```

Install dependencies:
```
pip install -r dev-requirements.txt
```

## Code quality commands
Formatting with black and isort (replace with viktor-cli.exe for Windows):
```
python -m black app/ tests/
python -m isort .
```

Static code analysis:
```
python -m pylint app/ tests/
python -m mypy app --ignore-missing-imports
```

Run tests:
```
./viktor-cli test $APP
```