#!/bin/bash

# Install packages from requirements.txt
pip install -r requirements.txt

# Download SpaCy language models
python -m spacy download es_core_news_md
python -m spacy download es

# Install averell and download dataset
pip install averell
#averell download adso100

