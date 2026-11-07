FROM python:3.14.10-slim
WORKDIR /app
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
RUN pip install --no-cache-dir --no-build-isolation --no-deps .
COPY tests ./tests
COPY scripts/matched-core-docker.sh ./scripts/matched-core-docker.sh
ENTRYPOINT ["python", "-m", "shape_dataset"]
