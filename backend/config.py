import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing setting {name}. Copy .env.example to .env and fill it in.")
    return value


# The database is a single file next to the code, no database server needed
DEFAULT_DB = Path(__file__).parent / "guessword.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")

# A short or guessable key would make the login tokens easy to fake
SECRET_KEY = _required("SECRET_KEY")
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be at least 32 characters long.")

TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "8"))

# Used only once, to create the first admin account
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
