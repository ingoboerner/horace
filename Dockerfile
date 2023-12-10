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

# Install Python dependencies
RUN pip install -r requirements.txt && \
    pip install averell && \
    averell download adso100 && \
    python -m spacy download es_core_news_md && \
    python -m spacy download es 
