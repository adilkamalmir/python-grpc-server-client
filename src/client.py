import lib
import yaml


if __name__ == '__main__':

    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    server = cfg['client']['server_ip'] + ':' + str(cfg['client']['server_port'])
    client = lib.FileClient(server)

    # demo for file uploading
    in_file_name = cfg['client']['input_file']
    client.upload(in_file_name)