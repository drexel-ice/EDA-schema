# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Development / runtime image for the EDA-Schema MCP server.
#
#   docker build -f docker/mcp/Dockerfile -t eda-schema-mcp:dev .
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/workspace eda-schema-mcp:dev pytest tests/mcp
#
# Run as your own user (--user) so files written into the mounted checkout are not owned by root.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    XDG_CACHE_HOME=/tmp/.cache \
    RUFF_CACHE_DIR=/tmp/.ruff_cache

# graphviz + headers are required to build pygraphviz (core requirement).
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential graphviz libgraphviz-dev make \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install dependencies first for layer caching.
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

# Copy the source and install it with the MCP extra.
COPY . .
RUN pip install -e ".[mcp]"

ENV EDA_SCHEMA_DATASET=/workspace/dataset/test
CMD ["eda-schema-mcp"]
