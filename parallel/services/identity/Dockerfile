FROM python:3.12-slim

WORKDIR /app

COPY . . 

RUN pip install uv 
RUN uv sync

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]