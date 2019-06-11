FROM python:2
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT [ "python", "dpdk-ip-pipeline-cli.py" ]
