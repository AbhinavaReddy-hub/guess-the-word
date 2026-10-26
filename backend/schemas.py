import re
from datetime import date

from pydantic import BaseModel, field_validator

SPECIAL_CHARS = "$%*@"


class RegisterIn(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def check_username(cls, value):
        if not re.fullmatch(r"[A-Za-z]{5,30}", value):
            raise ValueError("Username must be 5 to 30 letters (A-Z, a-z only).")
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        if not 5 <= len(value) <= 64 or len(value.encode()) > 72:
            raise ValueError("Password must be 5 to 64 characters.")
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("Password must have at least one letter.")
        if not re.search(r"\d", value):
            raise ValueError("Password must have at least one number.")
        if not any(c in SPECIAL_CHARS for c in value):
            raise ValueError("Password must have at least one of these: $ % * @")
        return value


class LoginIn(BaseModel):
    username: str
    password: str


class GuessIn(BaseModel):
    guess: str

    @field_validator("guess")
    @classmethod
    def check_guess(cls, value):
        if not re.fullmatch(r"[A-Z]{5}", value):
            raise ValueError("Guess must be exactly 5 capital letters.")
        return value


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class GuessOut(BaseModel):
    word: str
    colors: list[str]  # one of "green", "orange", "grey" for each letter


class GameOut(BaseModel):
    id: int
    status: str
    max_guesses: int
    hint: list[str]  # revealed letters in place, empty text for hidden ones
    guesses: list[GuessOut]


class StatusOut(BaseModel):
    games_today: int
    max_games: int
    active_game: GameOut | None


class DailyReportOut(BaseModel):
    date: date
    users: int
    correct_guesses: int


class UserReportRow(BaseModel):
    date: date
    words_tried: int
    correct_guesses: int
