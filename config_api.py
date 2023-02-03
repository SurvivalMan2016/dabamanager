import tomli

CONFIG = {
}


def load_config():
    """Loads configuration from config.ini file"""

    global CONFIG
    with open('res/config/config.ini', 'rb') as f:
        CONFIG = tomli.load(f)
