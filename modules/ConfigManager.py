import json
import logging
from json import JSONDecodeError
from pathlib import Path

from modules.helpers import is_json
from modules.models.ConfigFile import ConfigFile


class ConfigManager:
    _config: ConfigFile
    _config_path: Path

    def __init__(self, config_path: Path):
        self._config_path = config_path

    def load_config_from_file(self) -> ConfigFile | None:
        """
        This function loads the config from a json file
        :return: A ConfigFile instance if the provided file is valid, None otherwise
        """
        if self._config_path.exists() and self._config_path.is_file() and is_json(self._config_path):
            with open(self._config_path, mode="r") as config_fp:
                try:
                    self._config = json.load(config_fp, object_hook=ConfigFile)
                    if self.validate_config(self._config):
                        logging.info("Config file loaded successfully!")
                        return self._config
                    else:
                        logging.error(f"Unable to load config file, it seems invalid!")
                except JSONDecodeError as error:
                    logging.error(f"Unable to parse config file, error:\n {error.msg}")
        else:
            logging.error("Unable to locate config file because it do not exists or it is not a json file!")
        return None

    def load_config(self, config: ConfigFile) -> None:
        """
        This function load the provided ConfigFile for the runtime
        :param config: A validated ConfigFile instance
        """
        logging.info("Config updated successfully!")
        self._config = config

    def get_config(self) -> ConfigFile:
        """
        This function returns the current runtime config
        :return: A ConfigFile instance
        """
        return self._config

    def save_config_to_file(self) -> bool:
        """
        This function saves to the hard drive the current runtime config
        :return: True if the file is saved successfully, False otherwise
        """
        with open(self._config_path, mode="w") as config_fp:
            try:
                json.dump(self._config.__dict__, config_fp)
                logging.info("Config file saved successfully!")
                return True
            except JSONDecodeError as error:
                logging.error(f"Unable to save config file, error:\n {error.msg}")
        return False

    def validate_config(self, config: ConfigFile) -> bool:
        """
        This function check if the provided ConfigFile instance is valid
        :param config: A ConfigFile instance
        :return: True if the instance is valid, False otherwise
        """
        if not config.TG_SESSION or not config.TG_API_HASH or not config.TG_AUTHORIZED_USER_ID \
                or not config.TG_BOT_TOKEN or not config.TG_DOWNLOAD_PATH:
            return False
        if not self._validate_download_path(Path(config.TG_DOWNLOAD_PATH)):
            return False
        return True

    def _validate_download_path(self, download_path: Path) -> bool:
        """
        This function checks if the provided download path exists, and it is a directory
        :param download_path: A download path
        :return: True if the path is valid, False otherwise
        """
        if not download_path.exists() or not download_path.is_dir():
            logging.error("The provided download path is not valid!")
            return False
        return True

    def change_download_path(self, download_path: str) -> bool:
        if self._validate_download_path(Path(download_path)):
            logging.info(f"Changing download path to {download_path}")
            prev: str = self._config.TG_DOWNLOAD_PATH
            self._config.TG_DOWNLOAD_PATH = download_path
            if self.save_config_to_file():
                logging.info(f"Change success!")
                return True
            else:
                self._config.TG_DOWNLOAD_PATH = prev
        return False

    def change_max_parallel_downloads(self, max_dl: str) -> bool:
        try:
            max_int: int = int(max_dl)
            if max_int != self._config.TG_MAX_PARALLEL:
                logging.info(f"Changing max parallels downloads to {max_int}")
                self._config.TG_MAX_PARALLEL = max_int
            if self.save_config_to_file():
                logging.info(f"Change success!")
                return True
        except Exception:
            return False

