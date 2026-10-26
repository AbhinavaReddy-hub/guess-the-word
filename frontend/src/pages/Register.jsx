import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorMessage } from "../api";
import { checkPassword, checkUsername } from "../validation";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    const problem = checkUsername(username) || checkPassword(password);
    if (problem) return setError(problem);

    setError("");
    setBusy(true);
    try {
      const { data } = await api.post("/auth/register", { username, password });
      navigate("/login", { state: { message: data.message } });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card narrow" onSubmit={handleSubmit}>
      <h1>Create an account</h1>

      <label>
        Username
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
        <small>At least 5 letters, no numbers or spaces.</small>
      </label>
      <label>
        Password
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <small>At least 5 characters with a letter, a number and one of $ % * @</small>
      </label>

      {error && <p className="error">{error}</p>}
      <button className="primary" disabled={busy}>Register</button>
      <p className="hint">Already have an account? <Link to="/login">Log in</Link></p>
    </form>
  );
}
