# Step 1: Start with a base Docker image that we will build on
FROM python:3.13-slim

# Step 2: Get UV package manager binary from official image for virtual environment management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Step 3: set up the working directory inside the container
WORKDIR /app

#Step 4: Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Step 5: Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./

# Step 6: Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# Step 7: Copy application code
COPY pipeline.py pipeline.py

# Step 8: Set entry point
ENTRYPOINT ["uv", "run", "python", "pipeline.py"]