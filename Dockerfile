FROM python:3.12-slim

WORKDIR /code

ENV in_docker="true"

# install dependencies
RUN apt-get update && apt-get install -y build-essential 

# upgrade pip and build tools
RUN pip install --upgrade pip wheel setuptools

# copy what ever is needed
COPY pyproject.toml /code
COPY tmdb_service /code/tmdb_service
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint

# add manage_jobs to system path
COPY tmdb_service/manage_jobs.py /usr/local/bin/manage_jobs
RUN chmod 755 /usr/local/bin/manage_jobs /usr/local/bin/docker-entrypoint

# install project
RUN pip install .

ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["python", "-m", "tmdb_service.worker"]
