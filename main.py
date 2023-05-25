import json
from dnevnik_bot import run_bot

if __name__ == '__main__':
    with open("config.json", "r") as config_file:
        conf_vars = json.load(config_file)

    run_bot(conf_vars)
