import os


class Secrets:
    def __init__(self):
        self.S3_BUCKET_NAME = os.environ["ARDKR_S3_BUCKET_NAME"]
        self.S3_ENDPOINT_URL = os.environ["ARDKR_S3_ENDPOINT_URL"]
        self.S3_ACCESS_KEY_ID = os.environ["ARDKR_S3_ACCESS_KEY_ID"]
        self.S3_SECRET_ACCESS_KEY = os.environ["ARDKR_S3_SECRET_ACCESS_KEY"]
        self.OPEN_S3_BUCKET_NAME = os.environ["ARDKR_OPEN_S3_BUCKET_NAME"]
        self.OPEN_S3_ENDPOINT_URL = os.environ["ARDKR_OPEN_S3_ENDPOINT_URL"]
        self.OPEN_S3_ACCESS_KEY_ID = os.environ["ARDKR_OPEN_S3_ACCESS_KEY_ID"]
        self.OPEN_S3_SECRET_ACCESS_KEY = os.environ["ARDKR_OPEN_S3_SECRET_ACCESS_KEY"]
