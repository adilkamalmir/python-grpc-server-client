import lib
import yaml

if __name__ == '__main__':
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    lib.FileServer().start(cfg['server']['port'])
