import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api, { errorMessage, saveSession } from "../api";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const { data } = await api.post("/auth/login", { username, password });
      const session = { token: data.access_token, username: data.username, role: data.role };
      saveSession(session);
      onLogin(session);
      navigate(session.role === "admin" ? "/admin" : "/game");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card narrow" onSubmit={handleSubmit}>
      <h1>Log in</h1>
      {location.state?.message && <p className="notice">{location.state.message}</p>}

      <label>
        Username
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
      </label>
      <label>
        Password
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </label>

      {error && <p className="error">{error}</p>}
      <button className="primary" disabled={busy}>Log in</button>
      <p className="hint">New here? <Link to="/register">Create an account</Link></p>
    </form>
  );
}
