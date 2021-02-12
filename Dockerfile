FROM python:3.9
COPY requirements.txt /tmp/requirements.txt
RUN pip install -U -r /tmp/requirements.txt
COPY nodeinfo.py /nodeinfo.py

CMD python /nodeinfo.py
