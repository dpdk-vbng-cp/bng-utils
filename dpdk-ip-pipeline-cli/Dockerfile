FROM python:3
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "dpdk-ip-pipeline-cli.py" ]
