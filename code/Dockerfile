FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/v0.0/code

COPY . /workspace/v0.0/code

RUN chmod +x /workspace/v0.0/code/scripts/bootstrap_and_test.sh
RUN /workspace/v0.0/code/scripts/bootstrap_and_test.sh bootstrap-only

CMD ["bash"]
