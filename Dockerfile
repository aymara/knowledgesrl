FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

# Install SpaCy models for French and English
RUN python -m spacy download fr_core_news_md && \
    python -m spacy download en_core_web_md

ENV PYTHONPATH=/app/src:/app/src/nltk:/app
# Install NLTK corpora: VerbNet and FrameNet
RUN python -m nltk.downloader framenet_v15 verbnet wordnet

COPY src /app/src
COPY tests /app/tests
COPY data /app/data

RUN rm -Rf /app/src/nltk

CMD ["python", "-m", "unittest"]
