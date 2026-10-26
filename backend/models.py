from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10), default="player")  # "player" or "admin"


# "Rahul" and "rahul" should not be two different accounts
Index("ix_users_username_lower", func.lower(User.username), unique=True)


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(5), unique=True)


class Game(Base):
    """One word given to one player on one day."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    played_on: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(12), default="in_progress")  # in_progress, won, lost
    hint_positions: Mapped[str] = mapped_column(String(15), default="")  # e.g. "1,3"
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    word: Mapped[Word] = relationship()
    guesses: Mapped[list["Guess"]] = relationship(order_by="Guess.guess_no")


class Guess(Base):
    __tablename__ = "guesses"
    __table_args__ = (UniqueConstraint("game_id", "guess_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)
    guess_no: Mapped[int]
    text: Mapped[str] = mapped_column(String(5))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
