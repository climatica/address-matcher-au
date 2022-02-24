FROM debian:bullseye-slim

ARG DATA_URL="https://climatica-public.s3.ap-southeast-2.amazonaws.com/address-matching/gnaf_202111_offline.dmp"
# ARG DATA_URL="https://climatica-public.s3.ap-southeast-2.amazonaws.com/gnaf_offline_test.dmp"
ENV DATA_URL ${DATA_URL}

# Postgres user password - WARNING: change this to something a lot more secure
ARG pg_password="password"
ENV PGPASSWORD=${pg_password}

# get postgres signing key, add Postgres repo to apt and install Postgres with PostGIS
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y sudo wget gnupg2 curl python3-venv git \
  && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add - \
  && echo "deb http://apt.postgresql.org/pub/repos/apt/ bullseye-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list \
  && apt-get update \
  && apt-get install -y postgresql-13 postgresql-client-13 postgis postgresql-13-postgis-3 \
  && apt-get autoremove -y --purge \
  && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# start Postgres server and set the default user password
RUN /etc/init.d/postgresql start \
  && sudo -u postgres psql -c "ALTER USER postgres PASSWORD '${pg_password}';" \
  && sudo -u postgres psql -c "CREATE EXTENSION postgis;" \
  && /etc/init.d/postgresql stop

# download and restore GNAF Postgres dump files
RUN mkdir -p /data \
  && cd /data \
  && wget --quiet -O gnaf-offline.dmp ${DATA_URL} \
  && /etc/init.d/postgresql start \
  && pg_restore --no-owner --no-acl -Fc -d postgres -h localhost -p 5432 -U postgres /data/gnaf-offline.dmp \
  && /etc/init.d/postgresql stop \
  && rm /data/gnaf-offline.dmp

# enable external access to postgres - WARNING: these are insecure settings! Edit these to restrict access
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/13/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/13/main/postgresql.conf
EXPOSE 5432

# set user for postgres startup
USER postgres

# # Add VOLUMEs to allow backup of config, logs and databases
# VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Start postgres when starting the container
# CMD ["/usr/lib/postgresql/13/bin/postgres", "-D", "/var/lib/postgresql/13/main", "-c", "config_file=/etc/postgresql/13/main/postgresql.conf"]

# install poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -
# RUN curl -sSL https://install.python-poetry.org | python3 -
WORKDIR /app
COPY poetry.toml .
COPY pyproject.toml .
RUN $HOME/.poetry/bin/poetry install
# RUN $HOME/.local/bin/poetry install
COPY start.sh .
COPY main.py .

ENTRYPOINT ["/app/start.sh"]
