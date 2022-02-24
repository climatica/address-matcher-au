#!/bin/bash

/usr/lib/postgresql/13/bin/postgres -D /var/lib/postgresql/13/main -c config_file=/etc/postgresql/13/main/postgresql.conf &

$HOME/.poetry/bin/poetry run python /app/main.py $1
# $HOME/.local/bin/poetry run main.py $1
