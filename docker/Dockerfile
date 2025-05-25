FROM python:3-bullseye

WORKDIR /12-hour-server

RUN apt-get update && apt-get install -y sudo iputils-ping && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "smart_sleep.py" ]