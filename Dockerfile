FROM python:3.12-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN git clone https://github.com/pallets/flask.git . && \
    git checkout d73fa1cdcbd8b1465c151db8924ba58b1dd14e35

RUN pip install --no-cache-dir -e . pytest

COPY tests/test_nested_namespace.py tests/

CMD ["pytest", "tests/test_nested_namespace.py", "-v"]
