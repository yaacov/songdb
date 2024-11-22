.PHONY: lint lint-check test ssl clean all start image start-image

# Define the default goal
all: lint test

# Linting using black
lint:
	@echo "Running Black to lint the code..."
	black .

# Lint check (dry-run) using black to ensure code is properly formatted
lint-check:
	@echo "Running Black in check mode to verify formatting..."
	black --check .

# Running tests with pytest
test:
	@echo "Running tests with pytest..."
	pytest

# Generate SSL certificates for an HTTPS server
ssl:
	@if [ -f key.pem ] && [ -f cert.pem ]; then \
		echo "SSL certificates (key.pem and cert.pem) already exist. Skipping generation."; \
	else \
		echo "Generating SSL certificates (key.pem and cert.pem)..."; \
		python -c 'import subprocess; subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", "key.pem", "-out", "cert.pem", "-days", "365", "-nodes", "-subj", "/CN=localhost"])'; \
	fi

# Cleanup artifacts like compiled files, sqlite db, etc.
clean:
	@echo "Cleaning up compiled files and other artifacts..."
	python cleanup.py

# Start the Python server
start: ssl
	@echo "Starting Python server..."
	python server.py

# Build a container image
image:
	@echo "Building a container image..."
	podman build -t quay.io/yaacov/songdb -f Containerfile .

# Running a container image
start-image:
	@echo "Running a container image..."
	podman run --rm -p 8000:8000 -it quay.io/yaacov/songdb