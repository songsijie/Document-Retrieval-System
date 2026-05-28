import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

APP_ENV = os.getenv("APP_ENV", "dev").lower()

if APP_ENV == "dev":
    from .dev import *  # noqa: F403
elif APP_ENV == "prod":
    from .prod import *  # noqa: F403
else:
    msg = f"Invalid APP_ENV [{APP_ENV}], expected 'dev' or 'prod'"
    raise RuntimeError(msg)
