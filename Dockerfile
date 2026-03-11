FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Create the data directory
RUN mkdir -p /app/data
CMD ["python", "chaos_arena_bot.py"]
