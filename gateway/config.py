import os

from dotenv import load_dotenv


load_dotenv()


SCANNER_URL = os.getenv("SCANNER_URL")

if not SCANNER_URL:
    raise RuntimeError("SCANNER_URL is not configured")