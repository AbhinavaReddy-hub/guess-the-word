import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

const WORD_LENGTH = 5;

export default function Game() {
  const [info, setInfo] = useState(null); // games used today, daily limit
  const [game, setGame] = useState(null); // the game being played right now
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null); // "won" or "lost" while the popup is open

  async function loadStatus() {
    const { data } = await api.get("/game/status");
    setInfo(data);
    setGame(data.active_game);
  }

  useEffect(() => {
    loadStatus().catch((err) => setError(errorMessage(err)));
  }, []);

  async function startGame() {
    setError("");
    setBusy(true);
    try {
      const { data } = await api.post("/game/start");
      setGame(data);
      setText("");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function submitGuess(e) {
    e.preventDefault();
    if (text.length !== WORD_LENGTH) return setError("Type a word with exactly 5 letters.");

    setError("");
    setBusy(true);
    try {
      const { data } = await api.post(`/game/${game.id}/guess`, { guess: text });
      setGame(data);
      setText("");
      if (data.status !== "in_progress") setResult(data.status);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  // Clicking OK on the popup ends the game and goes back to the start screen
  async function closePopup() {
    setResult(null);
    setGame(null);
    setError("");
    try {
      await loadStatus();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  if (!info && !error) return <p>Loading...</p>;

  // ---- Start screen ----
  if (!game) {
    const outOfWords = info && info.games_today >= info.max_games;
    return (
      <section className="card narrow center">
        <h1>Ready to play?</h1>
        {info && (
          <p>You have played <strong>{info.games_today}</strong> of {info.max_games} words today.</p>
        )}
        {outOfWords && <p className="notice">You have used all your words for today. Come back tomorrow.</p>}
        {error && <p className="error">{error}</p>}
        <button className="primary" onClick={startGame} disabled={busy || outOfWords}>
          Start a new word
        </button>
      </section>
    );
  }

  // ---- Playing ----
  const playing = game.status === "in_progress";
  const rows = Array.from({ length: game.max_guesses }, (_, i) => {
    const done = game.guesses[i];
    if (done) return done.word.split("").map((letter, j) => ({ letter, color: done.colors[j] }));

    // The row being typed shows the letters so far
    const typing = playing && i === game.guesses.length ? text : "";
    return Array.from({ length: WORD_LENGTH }, (_, j) => ({ letter: typing[j] || "", color: "" }));
  });

  return (
    <section className="card center">
      <h1>Guess the word</h1>
      <p>Guess {Math.min(game.guesses.length + 1, game.max_guesses)} of {game.max_guesses}</p>

      <div className="hint">
        <p>Hint: some letters are shown</p>
        <div className="row">
          {game.hint.map((letter, i) => (
            <div className={`tile ${letter ? "revealed" : "hidden"}`} key={i}>{letter || "?"}</div>
          ))}
        </div>
      </div>

      <div className="board">
        {rows.map((row, i) => (
          <div className="row" key={i}>
            {row.map((tile, j) => (
              <div className={`tile ${tile.color}`} key={j}>{tile.letter}</div>
            ))}
          </div>
        ))}
      </div>

      <form className="guess-form" onSubmit={submitGuess}>
        <input
          className="guess-input"
          value={text}
          maxLength={WORD_LENGTH}
          disabled={!playing || busy}
          placeholder="TYPE HERE"
          autoFocus
          onChange={(e) => setText(e.target.value.toUpperCase().replace(/[^A-Z]/g, ""))}
        />
        <button className="primary" disabled={!playing || busy}>Guess</button>
      </form>
      {error && <p className="error">{error}</p>}

      <p className="legend">
        <span className="dot green" /> right spot
        <span className="dot orange" /> wrong spot
        <span className="dot grey" /> not in the word
      </p>

      {result && (
        <div className="overlay">
          <div className="modal" role="dialog" aria-modal="true">
            <h2>{result === "won" ? "Congratulations!" : "Better luck next time"}</h2>
            <p>{result === "won" ? "You guessed the word." : "You used all 5 guesses."}</p>
            <button className="primary" onClick={closePopup} autoFocus>OK</button>
          </div>
        </div>
      )}
    </section>
  );
}
