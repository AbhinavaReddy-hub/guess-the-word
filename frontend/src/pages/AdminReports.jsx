import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

// Today's date as YYYY-MM-DD in the browser's time zone
const todayString = () => new Date().toLocaleDateString("en-CA");

export default function AdminReports() {
  const [day, setDay] = useState(todayString());
  const [daily, setDaily] = useState(null);
  const [dailyError, setDailyError] = useState("");

  const [players, setPlayers] = useState([]);
  const [player, setPlayer] = useState("");
  const [rows, setRows] = useState(null);
  const [userError, setUserError] = useState("");

  useEffect(() => {
    api.get("/admin/players")
      .then(({ data }) => setPlayers(data))
      .catch((err) => setUserError(errorMessage(err)));
  }, []);

  async function runDaily(e) {
    e.preventDefault();
    setDailyError("");
    try {
      const { data } = await api.get("/admin/reports/daily", { params: { day } });
      setDaily(data);
    } catch (err) {
      setDaily(null);
      setDailyError(errorMessage(err));
    }
  }

  async function runUser(e) {
    e.preventDefault();
    setUserError("");
    try {
      const { data } = await api.get("/admin/reports/user", { params: { username: player } });
      setRows(data);
    } catch (err) {
      setRows(null);
      setUserError(errorMessage(err));
    }
  }

  return (
    <div className="reports">
      <section className="card">
        <h1>Report for a day</h1>
        <form className="inline-form" onSubmit={runDaily}>
          <input type="date" value={day} onChange={(e) => setDay(e.target.value)} required />
          <button className="primary">Show report</button>
        </form>
        {dailyError && <p className="error">{dailyError}</p>}
        {daily && (
          <table>
            <thead>
              <tr><th>Date</th><th>Number of users</th><th>Correct guesses</th></tr>
            </thead>
            <tbody>
              <tr><td>{daily.date}</td><td>{daily.users}</td><td>{daily.correct_guesses}</td></tr>
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h1>Report for a player</h1>
        <form className="inline-form" onSubmit={runUser}>
          <select value={player} onChange={(e) => setPlayer(e.target.value)} required>
            <option value="">Choose a player</option>
            {players.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button className="primary">Show report</button>
        </form>
        {userError && <p className="error">{userError}</p>}
        {rows && rows.length === 0 && <p>This player has not played yet.</p>}
        {rows && rows.length > 0 && (
          <table>
            <thead>
              <tr><th>Date</th><th>Words tried</th><th>Correct guesses</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.date}><td>{r.date}</td><td>{r.words_tried}</td><td>{r.correct_guesses}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
