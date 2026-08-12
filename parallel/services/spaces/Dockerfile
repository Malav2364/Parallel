FROM python:3.12-slim

WORKDIR /app

# Copy the pios_kernel and spaces service
COPY pios_kernel/ /app/pios_kernel/
COPY services/spaces/ /app/services/spaces/

WORKDIR /app/services/spaces

RUN pip install uv 
RUN uv sync

EXPOSE 8000

CMD ["uv","run","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
