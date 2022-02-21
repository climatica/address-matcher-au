# Getting Started

1. Run `poetry install` to install all basic requirements.
2. Install [gnaf-loader](https://github.com/minus34/gnaf-loader) using Docker.
   1. Pull the image using `docker pull minus34/gnafloader:latest`.
   2. Run using `docker run --publish=5433:5432 minus34/gnafloader:latest`.
3. Ensure the data is correct in `test.txt`.
4. Run project with `poetry run python main.py`.
