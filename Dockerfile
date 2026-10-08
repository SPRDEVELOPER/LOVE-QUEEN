FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
RUN useradd -m bot && chown -R bot /app
USER bot

# Render / Railway inject PORT; polling mode ignores it
EXPOSE 8080
CMD ["python", "-m", "src.main"]
