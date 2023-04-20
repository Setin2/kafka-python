FROM python:3.8

WORKDIR /app

# Good practice to copy just dependencies first; this helps
# layer caching when you repeat `docker build`.
# COPY source path is relative to the `docker build` directory,
# which we've set up to be the parent of the application source.
COPY service3/requirements.txt /app
# Use the cache if requirements.txt hasn't changed
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application from this folder
COPY service3 /app

# Copy the files shared by all images from the shared files folder
COPY shared-files /app

ENTRYPOINT ["python", "service3.py"]
CMD []