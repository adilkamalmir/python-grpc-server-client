FROM python:3.6.5

WORKDIR /usr/src/app

RUN python -m pip install grpcio
RUN python -m pip install grpcio-tools
RUN python -m pip install PyYAML
RUN python -m pip install kafka
RUN python -m pip install futures
RUN apt-get update
RUN apt-get install vim -y

COPY src ./

CMD [ "python", "./server.py" ]
