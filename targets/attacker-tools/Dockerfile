FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlmap hydra nmap curl jq ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab

CMD ["sleep", "infinity"]
