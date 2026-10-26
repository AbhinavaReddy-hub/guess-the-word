import { useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { clearSession, getSession } from "./api";
import AdminReports from "./pages/AdminReports.jsx";
import Game from "./pages/Game.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";

// Where each kind of user lands after logging in
const homeFor = (session) => (session?.role === "admin" ? "/admin" : "/game");

export default function App() {
  const [session, setSession] = useState(getSession());
  const navigate = useNavigate();

  function logout() {
    clearSession();
    setSession(null);
    navigate("/login");
  }

  // Only let the right role into a page
  function Protected({ role, children }) {
    if (!session) return <Navigate to="/login" replace />;
    if (session.role !== role) return <Navigate to={homeFor(session)} replace />;
    return children;
  }

  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">Guess the Word</Link>
        {session && (
          <div className="who">
            <span>{session.username}</span>
            <button className="link-button" onClick={logout}>Log out</button>
          </div>
        )}
      </header>

      <main className="page">
        <Routes>
          <Route path="/login" element={<Login onLogin={setSession} />} />
          <Route path="/register" element={<Register />} />
          <Route path="/game" element={<Protected role="player"><Game /></Protected>} />
          <Route path="/admin" element={<Protected role="admin"><AdminReports /></Protected>} />
          <Route path="*" element={<Navigate to={session ? homeFor(session) : "/login"} replace />} />
        </Routes>
      </main>
    </>
  );
}
