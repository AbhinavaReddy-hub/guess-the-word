import os

# Settings must exist before the app is imported. Tests use an in-memory SQLite database.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-123"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import seed
from auth import hash_password
from database import Base, get_db
from game import check_guess
from main import app
from models import Game, User, Word
from schemas import GuessIn, RegisterIn

PLAYER = {"username": "Rahulkumar", "password": "pass$123"}


# ---------- Colour logic ----------

def test_all_green():
    assert check_guess("APPLE", "APPLE") == ["green"] * 5


def test_all_grey():
    assert check_guess("APPLE", "TIGHT") == ["grey"] * 5


def test_wrong_place_is_orange():
    assert check_guess("APPLE", "PAPER") == ["orange", "orange", "green", "orange", "grey"]


def test_repeated_letter_is_not_over_counted():
    # LEMON has one L, so only the first L (right place) is coloured
    assert check_guess("LEMON", "LLLLL") == ["green", "grey", "grey", "grey", "grey"]


# ---------- Input rules ----------

def test_seed_words_are_valid():
    assert len(seed.WORDS) == 20
    assert len(set(seed.WORDS)) == 20
    assert all(len(w) == 5 and w.isalpha() and w.isupper() for w in seed.WORDS)


@pytest.mark.parametrize("name", ["abcd", "abc1def", "ab cde", "a" * 31])
def test_bad_usernames(name):
    with pytest.raises(ValueError):
        RegisterIn(username=name, password="pass$123")


@pytest.mark.parametrize("pw", ["ab$1", "abcdef$$", "abc123", "123$%*", "abc123!"])
def test_bad_passwords(pw):
    with pytest.raises(ValueError):
        RegisterIn(username="Rahulkumar", password=pw)


@pytest.mark.parametrize("pw", ["abc1$", "Pass%99", "xy*12", "a1@bc"])
def test_good_passwords(pw):
    RegisterIn(username="Rahulkumar", password=pw)


@pytest.mark.parametrize("guess", ["apple", "APPL", "APPLES", "APP1E", "AP LE"])
def test_bad_guesses(guess):
    with pytest.raises(ValueError):
        GuessIn(guess=guess)


# ---------- Whole flow through the API ----------

@pytest.fixture()
def env():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    with Session() as db:
        db.add_all(Word(text=w) for w in seed.WORDS)
        db.add(User(username="Adminuser", password_hash=hash_password("Admin$123"), role="admin"))
        db.commit()

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app), Session
    app.dependency_overrides.clear()


def login(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def register_and_login(client, creds=PLAYER):
    assert client.post("/api/auth/register", json=creds).status_code == 201
    return login(client, creds["username"], creds["password"])


def secret_of(Session, game_id):
    with Session() as db:
        return db.get(Game, game_id).word.text


def lose_a_game(client, headers):
    game = client.post("/api/game/start", headers=headers).json()
    for _ in range(5):
        game = client.post(f"/api/game/{game['id']}/guess", json={"guess": "ZZZZZ"}, headers=headers).json()
    return game


def test_register_rules_and_duplicates(env):
    client, _ = env
    assert client.post("/api/auth/register", json={"username": "abc", "password": "pass$123"}).status_code == 422
    assert client.post("/api/auth/register", json=PLAYER).status_code == 201
    same_name_other_case = {"username": "RAHULKUMAR", "password": "pass$123"}
    assert client.post("/api/auth/register", json=same_name_other_case).status_code == 409


def test_login_wrong_password(env):
    client, _ = env
    client.post("/api/auth/register", json=PLAYER)
    res = client.post("/api/auth/login", json={"username": PLAYER["username"], "password": "wrong$1"})
    assert res.status_code == 401


def test_game_needs_login(env):
    client, _ = env
    assert client.post("/api/game/start").status_code == 401
    assert client.get("/api/game/status", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_win_flow_and_secret_is_hidden(env):
    client, Session = env
    headers = register_and_login(client)

    game = client.post("/api/game/start", headers=headers).json()
    assert game["status"] == "in_progress" and game["guesses"] == []
    secret = secret_of(Session, game["id"])

    wrong = "ZZZZZ"
    game = client.post(f"/api/game/{game['id']}/guess", json={"guess": wrong}, headers=headers).json()
    assert game["guesses"][0]["colors"] == ["grey"] * 5
    assert secret not in str(game)

    game = client.post(f"/api/game/{game['id']}/guess", json={"guess": secret}, headers=headers).json()
    assert game["status"] == "won"
    assert [g["word"] for g in game["guesses"]] == [wrong, secret]

    # A finished game takes no more guesses
    res = client.post(f"/api/game/{game['id']}/guess", json={"guess": secret}, headers=headers)
    assert res.status_code == 400


def test_hint_shows_two_letters_and_stays_the_same(env):
    client, Session = env
    headers = register_and_login(client)
    game = client.post("/api/game/start", headers=headers).json()
    secret = secret_of(Session, game["id"])

    shown = [(i, c) for i, c in enumerate(game["hint"]) if c]
    assert len(game["hint"]) == 5 and len(shown) == 2
    assert all(secret[i] == c for i, c in shown)

    # Resuming the game gives the same hint
    again = client.post("/api/game/start", headers=headers).json()
    assert again["hint"] == game["hint"]


def test_lose_after_five_guesses(env):
    client, _ = env
    headers = register_and_login(client)
    game = lose_a_game(client, headers)
    assert game["status"] == "lost" and len(game["guesses"]) == 5


def test_unfinished_game_is_resumed_not_restarted(env):
    client, _ = env
    headers = register_and_login(client)
    first = client.post("/api/game/start", headers=headers).json()
    client.post(f"/api/game/{first['id']}/guess", json={"guess": "ZZZZZ"}, headers=headers)

    second = client.post("/api/game/start", headers=headers).json()
    assert second["id"] == first["id"] and len(second["guesses"]) == 1
    assert client.get("/api/game/status", headers=headers).json()["games_today"] == 1


def test_three_words_per_day_limit(env):
    client, _ = env
    headers = register_and_login(client)
    for _ in range(3):
        lose_a_game(client, headers)
    res = client.post("/api/game/start", headers=headers)
    assert res.status_code == 403


def test_player_cannot_play_someone_elses_game(env):
    client, _ = env
    mine = register_and_login(client)
    other = register_and_login(client, {"username": "Otherplayer", "password": "pass$123"})
    game = client.post("/api/game/start", headers=mine).json()
    res = client.post(f"/api/game/{game['id']}/guess", json={"guess": "ZZZZZ"}, headers=other)
    assert res.status_code == 404


def test_roles_are_separated(env):
    client, _ = env
    player = register_and_login(client)
    admin = login(client, "Adminuser", "Admin$123")
    assert client.get("/api/admin/reports/daily", headers=player).status_code == 403
    assert client.post("/api/game/start", headers=admin).status_code == 403


def test_admin_reports(env):
    client, Session = env
    first = register_and_login(client)
    second = register_and_login(client, {"username": "Otherplayer", "password": "pass$123"})
    admin = login(client, "Adminuser", "Admin$123")

    # First player wins one word and loses one. Second player wins one.
    game = client.post("/api/game/start", headers=first).json()
    client.post(f"/api/game/{game['id']}/guess", json={"guess": secret_of(Session, game["id"])}, headers=first)
    lose_a_game(client, first)
    game = client.post("/api/game/start", headers=second).json()
    client.post(f"/api/game/{game['id']}/guess", json={"guess": secret_of(Session, game["id"])}, headers=second)

    daily = client.get("/api/admin/reports/daily", headers=admin).json()
    assert daily["users"] == 2 and daily["correct_guesses"] == 2

    rows = client.get("/api/admin/reports/user", params={"username": PLAYER["username"]}, headers=admin).json()
    assert len(rows) == 1 and rows[0]["words_tried"] == 2 and rows[0]["correct_guesses"] == 1

    assert client.get("/api/admin/reports/user", params={"username": "Nobodyhere"}, headers=admin).status_code == 404
    assert client.get("/api/admin/players", headers=admin).json() == ["Otherplayer", "Rahulkumar"]
