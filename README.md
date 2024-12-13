## FastAPI User Registration/Login App


### Table of Contents

### Project Overview

### Features

### Installation Guide

You need following to run this project:

- Python 3.11
- [Docker with Docker Compose](https://docs.docker.com/compose/install/)

Follow the below steps to get the project up and running:
1. Install pipenv if not available
```bash
pip install pipenv==2024.1.0
```
2. Activate Shell
```bash
pipenv --python 3.11.3 shell # ubuntu
```
3. Pipfile File
```bash
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
fastapi = "*"
uvicorn = "*"
sqlmodel = "*"
psycopg2-binary = "*"
python-jose = "*"
passlib = "*"
email-validator = "*"
bcrypt = "*"

[requires]
python_version = "3.11"
```
4. Install Dependencies with **pipenv**
- Install regular dependencies:
```bash
pipenv install
```
4. Verify Virtual Environment
```bash
pipenv graph
```
5. Run docker compose file
- Start the database:
```bash
docker-compose up -d
```
5. Run Your FastAPI App
- python -m app.main



The server should now be running on `http://localhost:8000` and the API documentation should be available at `http://localhost:8000/docs`.

### Usage Guide

