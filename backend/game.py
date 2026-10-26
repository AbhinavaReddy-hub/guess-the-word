import random
import threading
from collections import Counter
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Game, Guess, User, Word

WORD_LENGTH = 5
MAX_GUESSES = 5
MAX_GAMES_PER_DAY = 3
HINT_LETTERS = 2  # how many letters are shown at the start

# SQLite has no row locks. This lock stops two quick requests from running at the same
# time, so nobody can sneak past the daily limit or double-submit a guess.
write_lock = threading.Lock()


def check_guess(secret: str, guess: str) -> list[str]:
    """Colour each letter of the guess: green, orange or grey."""
    colors = ["grey"] * len(guess)
    unmatched = Counter()

    # First pass: letters in the right place
    for i, (s, g) in enumerate(zip(secret, guess)):
        if s == g:
            colors[i] = "green"
        else:
            unmatched[s] += 1

    # Second pass: right letter, wrong place. Each secret letter can only be used once,
    # so a repeated letter in the guess doesn't turn orange more often than it should.
    for i, g in enumerate(guess):
        if colors[i] != "green" and unmatched[g] > 0:
            colors[i] = "orange"
            unmatched[g] -= 1

    return colors


def game_to_dict(game: Game) -> dict:
    # The browser only gets the hint letters and the colours, never the whole word
    shown = {int(i) for i in game.hint_positions.split(",") if i}
    return {
        "id": game.id,
        "status": game.status,
        "max_guesses": MAX_GUESSES,
        "hint": [letter if i in shown else "" for i, letter in enumerate(game.word.text)],
        "guesses": [
            {"word": g.text, "colors": check_guess(game.word.text, g.text)} for g in game.guesses
        ],
    }


def games_today_count(db: Session, user: User) -> int:
    return db.scalar(
        select(func.count()).select_from(Game).where(Game.user_id == user.id, Game.played_on == date.today())
    )


def active_game_today(db: Session, user: User) -> Game | None:
    return db.scalar(
        select(Game).where(
            Game.user_id == user.id, Game.played_on == date.today(), Game.status == "in_progress"
        )
    )


def start_game(db: Session, user: User) -> Game:
    with write_lock:
        return _start_game(db, user)


def _start_game(db: Session, user: User) -> Game:
    # If a game is still open, continue it instead of using up another word
    game = active_game_today(db, user)
    if game:
        return game

    if games_today_count(db, user) >= MAX_GAMES_PER_DAY:
        raise HTTPException(
            status_code=403,
            detail=f"You have used all {MAX_GAMES_PER_DAY} words for today. Come back tomorrow.",
        )

    word_ids = db.scalars(select(Word.id)).all()
    if not word_ids:
        raise HTTPException(status_code=500, detail="No words are available.")

    # Pick which letter positions to show as the hint
    hint = sorted(random.sample(range(WORD_LENGTH), HINT_LETTERS))
    game = Game(
        user_id=user.id,
        word_id=random.choice(word_ids),
        played_on=date.today(),
        hint_positions=",".join(str(i) for i in hint),
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def submit_guess(db: Session, user: User, game_id: int, text: str) -> Game:
    with write_lock:
        return _submit_guess(db, user, game_id, text)


def _submit_guess(db: Session, user: User, game_id: int, text: str) -> Game:
    game = db.scalar(select(Game).where(Game.id == game_id, Game.user_id == user.id))
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    if game.status != "in_progress":
        raise HTTPException(status_code=400, detail="This game is already finished.")

    guess_no = len(game.guesses) + 1
    db.add(Guess(game_id=game.id, guess_no=guess_no, text=text))

    if text == game.word.text:
        game.status = "won"
    elif guess_no >= MAX_GUESSES:
        game.status = "lost"

    db.commit()
    db.refresh(game)
    return game
