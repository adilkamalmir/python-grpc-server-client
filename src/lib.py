import yaml
import grpc
import time
from concurrent import futures
from kafka import KafkaProducer

import mdt_grpc_dialout_pb2, mdt_grpc_dialout_pb2_grpc

CHUNK_SIZE = 16601


def get_file_chunks(filename):
    with open(filename, 'rb') as f:
        while True:
            piece = f.read(CHUNK_SIZE)
            if len(piece) == 0:
                return
            yield mdt_grpc_dialout_pb2.MdtDialoutArgs(data=piece)


def publish_message(producer_instance, topic_name, key, value):
    try:
        key_bytes = bytes(key, encoding='utf-8')
        producer_instance.send(topic_name, key=key_bytes, value=value.data)
        producer_instance.flush()
        print('Message published successfully.')
    except Exception as ex:
        print('Exception in publishing message')
        print(str(ex))


def connect_kafka_producer(server):
    _producer = None
    try:
        _producer = KafkaProducer(bootstrap_servers=[server], api_version=(0, 10))
    except Exception as ex:
        print('Exception while connecting Kafka')
        print(str(ex))
    finally:
        return _producer


class FileClient:
    def __init__(self, address):
        channel = grpc.insecure_channel(address)
        self.stub = mdt_grpc_dialout_pb2_grpc.gRPCMdtDialoutStub(channel)

    def upload(self, in_file_name):
        chunks_generator = get_file_chunks(in_file_name)
        response = self.stub.MdtDialout(chunks_generator)
        try:
            print(next(response))
        except Exception as e:
            if str(e).find("EOF") != -1:
                print("sent")
                exit()
        except KeyboardInterrupt:
            exit()


class FileServer(mdt_grpc_dialout_pb2_grpc.gRPCMdtDialoutServicer):
    def __init__(self):

        class Servicer(mdt_grpc_dialout_pb2_grpc.gRPCMdtDialoutServicer):
            def __init__(self):
                with open("config.yml", 'r') as ymlfile:
                    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
                self.tmp_file_name = cfg['server']['output_file']
                self.kafka_topic = cfg['server']['kafka_topic']
                self.kafka_server = cfg['server']['kafka_server']
                self.kafka_producer = connect_kafka_producer(self.kafka_server)

            def MdtDialout(self, request_iterator, context):
                with open(self.tmp_file_name, 'wb') as f:
                    for item in request_iterator:
                        print(item.data)
                        f.write(item.data)
                        publish_message(self.kafka_producer, self.kafka_topic, 'raw', item)
                yield mdt_grpc_dialout_pb2.MdtDialoutArgs(errors="done")

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        mdt_grpc_dialout_pb2_grpc.add_gRPCMdtDialoutServicer_to_server(Servicer(), self.server)

    def start(self, port):
        self.server.add_insecure_port(f'[::]:{port}')
        self.server.start()

        try:
            while True:
                time.sleep(60*60*24)
        except KeyboardInterrupt:
            self.server.stop(0)
