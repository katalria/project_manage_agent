FROM python:3.11.7-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry
RUN poetry config virtualenvs.create false \
    && poetry install --only=main

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["python", "src/main.py"]