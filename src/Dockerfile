FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
LABEL authors="giumartine"

WORKDIR /home
COPY . .

RUN uv init
RUN uv add -r ./requirements.txt

CMD [".venv/bin/fastapi", "run", "main.py", "--port", "8000"]