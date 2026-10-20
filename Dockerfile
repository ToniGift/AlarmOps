# AlarmOps simulated alarm service. SIMULATION ONLY; reads a CSV replay stream.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir .
COPY alarms.yaml ./
COPY data/replay.csv ./data/replay.csv
RUN useradd --create-home appuser
USER appuser
CMD ["python", "-m", "alarmops.service", "--rules", "alarms.yaml", "--data", "data/replay.csv"]
