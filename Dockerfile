# The agent factory: an AI agent that designs and builds other CrewAI crews.
#
#   docker build -t agent-factory .
#   docker run --rm --env-file .env -v "$PWD/generated:/app/generated" \
#       agent-factory "Research a company and write an investment briefing"
#
# Generated projects and crew output land in bind-mounted directories so they
# survive the container. Nothing is baked into the image.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first: this layer is the slow one, and it only rebuilds when
# requirements.txt changes rather than on every source edit.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agent_factory/ ./agent_factory/
COPY main.py ./

# Run as a non-root user whose uid matches the typical host user, so files
# written into bind-mounted volumes stay editable on the host.
RUN useradd --create-home --uid 1000 factory \
    && mkdir -p /app/generated /app/workspace \
    && chown -R factory:factory /app
USER factory

# CrewAI writes telemetry/config under $HOME; give it a writable one.
ENV HOME=/home/factory

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
