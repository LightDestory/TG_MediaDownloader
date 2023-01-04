class ConfigFile:
    TG_SESSION: str
    TG_API_ID: int
    TG_API_HASH: str
    TG_BOT_TOKEN: str
    TG_DOWNLOAD_PATH: str
    TG_MAX_PARALLEL: int
    TG_DL_TIMEOUT: int
    TG_AUTHORIZED_USER_ID: list[int]

    def __init__(self, data=None):
        if data is None:
            return
        self.TG_SESSION = data['TG_SESSION']
        self.TG_API_ID = data['TG_API_ID']
        self.TG_API_HASH = data['TG_API_HASH']
        self.TG_BOT_TOKEN = data['TG_BOT_TOKEN']
        self.TG_DOWNLOAD_PATH = data['TG_DOWNLOAD_PATH']
        self.TG_MAX_PARALLEL = data['TG_MAX_PARALLEL']
        self.TG_DL_TIMEOUT = data['TG_DL_TIMEOUT']
        self.TG_AUTHORIZED_USER_ID = data['TG_AUTHORIZED_USER_ID']
