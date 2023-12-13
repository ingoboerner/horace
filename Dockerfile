# Use this Dockerfile to work exclusively from the container
# as it copies the project
FROM python:3.7-buster

WORKDIR /workspaces/horace

# Copy the current directory contents into the container
COPY . /workspaces/horace

# Install system dependencies
RUN apt update && \
    apt install -y git && \
    rm -rf /var/lib/apt/lists/*

# Install requirements
RUN bash install-requirements.sh

RUN mkdir out

# for debugging purposes, keeps the container running
ENTRYPOINT ["tail", "-f", "/dev/null"]

