FROM python:3.13.2-slim

WORKDIR /app

# Install Poetry
RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://install.python-poetry.org | python3 -
# Add Poetry to the PATH
ENV PATH="$PATH:/root/.local/bin"
# Set up Poetry configuration to not create a virtual env
RUN poetry config virtualenvs.create false --local 

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy application code
COPY . .

# Expose the port
EXPOSE 8080

# Run the application
CMD ["python3", "main.py"]