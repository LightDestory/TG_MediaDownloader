import logging
import os
import time
from pathlib import Path

from modules.models.ConfigFile import ConfigFile


def get_env(name: str, message: str, is_int: bool = False) -> int | str:
    """
    This function prompts the user to enter an information
    :param name: Corresponding environment variable name
    :param message: The message to shows to the user
    :param is_int: A control flag to cast the entered value as a integer
    :return: A string or integer
    """
    if name in os.environ:
        return os.environ[name]
    while True:
        try:
            user_value: str = input(message)
            if is_int:
                return int(user_value)
            return user_value
        except KeyboardInterrupt:
            print("\n")
            logging.info("Invoked interrupt during input request, closing process...")
            exit(-1)
        except ValueError as e:
            logging.error(e)
            time.sleep(1)


def get_config_from_user() -> ConfigFile:
    """
    This function ask the user to enter the needed information
    :return: A ConfigFile instance
    """
    config: ConfigFile = ConfigFile()
    config.TG_SESSION = os.environ.get('TG_SESSION', 'tg_downloader')
    config.TG_API_ID = get_env('TG_API_ID', 'Enter your API ID: ', True)
    config.TG_API_HASH = get_env('TG_API_HASH', 'Enter your API hash: ')
    config.TG_BOT_TOKEN = get_env('TG_BOT_TOKEN', 'Enter your Telegram BOT token: ')
    config.TG_DOWNLOAD_PATH = get_env('TG_DOWNLOAD_PATH', 'Enter full path to downloads directory: ')
    config.TG_MAX_PARALLEL = int(os.environ.get('TG_MAX_PARALLEL', 4))
    config.TG_DL_TIMEOUT = int(os.environ.get('TG_DL_TIMEOUT', 5400))
    while True:
        authorized_users = get_env('TG_AUTHORIZED_USER_ID',
                                   "Enter the list authorized users' id (separated by comma, can't be empty): ")
        authorized_users = [int(user_id) for user_id in authorized_users.split(",")] if authorized_users else []
        if authorized_users:
            config.TG_AUTHORIZED_USER_ID = authorized_users
            break
    return config


def is_json(file: Path) -> bool:
    """
    This function check if the file extension is 'json'
    :param file: A Path to an existing file
    :return: True if the file's extension is json, False otherwise
    """
    return file.name.split(".")[-1] == "json"
