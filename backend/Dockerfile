# Use a slim official Python base image -- smaller footprint, faster builds,
# and fewer OS packages to worry about from a security standpoint.
FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr,
# so logs appear immediately in `docker logs` instead of being buffered.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first, separately from the rest of the app code.
# Docker caches each layer -- as long as requirements.txt doesn't change,
# this pip install layer is reused on rebuilds instead of re-running,
# making iterative builds much faster.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code.
COPY app/ ./app/

# Document that the container listens on port 8000 (informational --
# doesn't actually publish the port; that happens at `docker run`).
EXPOSE 8000

# Run without --reload in production -- reload is a dev-only feature
# that watches the filesystem for changes, which adds overhead and
# isn't relevant inside an immutable container image.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]