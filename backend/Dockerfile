FROM python:3.11-slim

WORKDIR /app

# install build tools & client for waiting on Postgres
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy application code
COPY . .
RUN chmod +x /app/start.sh

# expose port and provide default command
EXPOSE 8000

CMD ["/app/start.sh"]
