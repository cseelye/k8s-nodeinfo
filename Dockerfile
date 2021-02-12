FROM python:3.9
COPY requirements.txt /tmp/requirements.txt
RUN pip install -U -r /tmp/requirements.txt
