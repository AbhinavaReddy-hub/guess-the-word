# Guess the Word

A small Wordle-style game. Players guess a 5-letter word in 5 tries, and admins see reports.

**Stack:** FastAPI, SQLAlchemy, SQLite, JWT (backend) and React with Vite (frontend).

## What you need

- Python 3.11 or newer
- Node.js 18 or newer

No database server is needed. SQLite saves everything in one file, `backend/guessword.db`.

## Setup on Windows

### 1. Start the backend

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and fill in a secret key and the admin password. To make a secret key:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Then run:

```
uvicorn main:app --reload
```

On first start it creates the database file, the tables, adds the 20 words, and creates the admin account from `.env`.
API docs are at http://localhost:8000/docs

### 2. Start the frontend (new terminal)

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 3. Run the tests

```
cd backend
venv\Scripts\activate
pytest
```

The tests use a temporary in-memory database, so they don't touch your real data.

## How it works

- **Register:** username is 5+ letters only. Password is 5+ characters with a letter, a number, and one of `$ % * @`. New accounts are always players.
- **Admin:** created once from `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`. Admins see reports but don't play.
- **Playing:** each player gets up to 3 words a day. Each word allows 5 guesses (5 capital letters). Colours: green = right spot, orange = wrong spot, grey = not in the word. A game left unfinished is continued, not replaced, and it still counts as one of the 3 words.
- **Saved data:** every game (player, word, date, result) and every guess is stored in the SQLite database.
- **Note:** run the backend as a single process (the default `uvicorn main:app`). The daily-limit lock works inside one process.
- **Reports:** by day (number of users, correct guesses) and by player (date, words tried, correct guesses).

## Security notes

- Passwords are hashed with bcrypt.
- Login uses a signed JWT. The role is checked against the database on every request.
- The secret word is never sent to the browser. Colours are worked out on the server.
- Login errors don't say whether the username or the password was wrong.
- Secrets live in `.env`, which is git-ignored.

## Folder layout

```
backend/    main.py (routes), models.py, schemas.py, auth.py, game.py, seed.py, test_game.py
frontend/   src/App.jsx, src/api.js, src/pages/ (Login, Register, Game, AdminReports)
```
