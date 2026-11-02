FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /usr/local/bin/uv

WORKDIR /opt/pr-reviewer
COPY pyproject.toml uv.lock README.md ./
COPY reviewer ./reviewer
RUN uv pip install --system --no-cache .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
