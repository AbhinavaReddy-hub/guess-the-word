from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import game
import seed
from auth import (
    DUMMY_HASH,
    create_token,
    hash_password,
    require_admin,
    require_player,
    verify_password,
)
from database import get_db
from models import Game, User
from schemas import (
    DailyReportOut,
    GameOut,
    GuessIn,
    LoginIn,
    RegisterIn,
    StatusOut,
    TokenOut,
    UserReportRow,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed.run()
    yield


app = FastAPI(title="Guess the Word", lifespan=lifespan)


def find_user(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.username) == username.lower()))


# ---------- Accounts ----------

@app.post("/api/auth/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if find_user(db, data.username):
        raise HTTPException(status_code=409, detail="That username is already taken.")

    db.add(User(username=data.username, password_hash=hash_password(data.password), role="player"))
    try:
        db.commit()
    except IntegrityError:  # someone registered the same name a split second earlier
        db.rollback()
        raise HTTPException(status_code=409, detail="That username is already taken.")
    return {"message": "Account created. You can log in now."}


@app.post("/api/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = find_user(db, data.username)
    password_ok = verify_password(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not password_ok:
        # Same message for both cases, so nobody can use it to find valid usernames
        raise HTTPException(status_code=401, detail="Wrong username or password.")
    return TokenOut(access_token=create_token(user.id), username=user.username, role=user.role)


# ---------- Player: the game ----------

@app.get("/api/game/status", response_model=StatusOut)
def game_status(user: User = Depends(require_player), db: Session = Depends(get_db)):
    active = game.active_game_today(db, user)
    return {
        "games_today": game.games_today_count(db, user),
        "max_games": game.MAX_GAMES_PER_DAY,
        "active_game": game.game_to_dict(active) if active else None,
    }


@app.post("/api/game/start", response_model=GameOut)
def start_game(user: User = Depends(require_player), db: Session = Depends(get_db)):
    return game.game_to_dict(game.start_game(db, user))


@app.post("/api/game/{game_id}/guess", response_model=GameOut)
def submit_guess(
    game_id: int, data: GuessIn, user: User = Depends(require_player), db: Session = Depends(get_db)
):
    return game.game_to_dict(game.submit_guess(db, user, game_id, data.guess))


# ---------- Admin: reports ----------

@app.get("/api/admin/players", response_model=list[str])
def list_players(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.scalars(select(User.username).where(User.role == "player").order_by(User.username)).all()


@app.get("/api/admin/reports/daily", response_model=DailyReportOut)
def daily_report(day: date | None = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    day = day or date.today()
    users = db.scalar(select(func.count(func.distinct(Game.user_id))).where(Game.played_on == day))
    correct = db.scalar(
        select(func.count()).select_from(Game).where(Game.played_on == day, Game.status == "won")
    )
    return {"date": day, "users": users, "correct_guesses": correct}


@app.get("/api/admin/reports/user", response_model=list[UserReportRow])
def user_report(username: str, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = find_user(db, username)
    if user is None or user.role != "player":
        raise HTTPException(status_code=404, detail="Player not found.")

    rows = db.execute(
        select(
            Game.played_on,
            func.count(Game.id),
            func.count(case((Game.status == "won", 1))),  # counts only the won games
        )
        .where(Game.user_id == user.id)
        .group_by(Game.played_on)
        .order_by(Game.played_on.desc())
    ).all()
    return [{"date": d, "words_tried": tried, "correct_guesses": won} for d, tried, won in rows]
