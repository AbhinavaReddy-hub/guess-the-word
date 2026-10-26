from sqlalchemy import func, select

import config
from auth import hash_password
from database import Base, SessionLocal, engine
from models import User, Word
from schemas import RegisterIn

WORDS = [
    "APPLE", "BRAVE", "CHAIR", "DREAM", "EAGLE", "FLAME", "GRAPE", "HOUSE", "IMAGE", "JOLLY",
    "KNIFE", "LEMON", "MANGO", "NIGHT", "OCEAN", "PLANT", "QUICK", "RIVER", "SMILE", "TIGER",
]


def run():
    """Create tables, add the starting words and the first admin. Safe to run many times."""
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Word)) == 0:
            db.add_all(Word(text=w) for w in WORDS)

        if config.ADMIN_USERNAME and config.ADMIN_PASSWORD:
            exists = db.scalar(
                select(User.id).where(func.lower(User.username) == config.ADMIN_USERNAME.lower())
            )
            if not exists:
                # Same username and password rules as everyone else
                creds = RegisterIn(username=config.ADMIN_USERNAME, password=config.ADMIN_PASSWORD)
                db.add(User(username=creds.username, password_hash=hash_password(creds.password), role="admin"))

        db.commit()
