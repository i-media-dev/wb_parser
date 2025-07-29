FROM python:3.13-slim
RUN apt-get update && apt-get install -y cron tzdata && \
    ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY crontab /etc/cron.d/wb-parser-cron
RUN chmod 0644 /etc/cron.d/wb-parser-cron && \
    crontab /etc/cron.d/wb-parser-cron && \
    touch /var/log/cron.log
CMD cron && tail -f /var/log/cron.log
