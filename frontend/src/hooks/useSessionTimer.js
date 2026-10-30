import { useEffect, useState } from "react";

const SESSION_MS = 2 * 60 * 60 * 1000;

export function useSessionTimer(user) {
  const [remaining, setRemaining] = useState(SESSION_MS);
  useEffect(() => {
    if (!user?.visitante) return undefined;
    const startedAt =
      Number(localStorage.getItem("guia_session_started")) || Date.now();
    localStorage.setItem("guia_session_started", String(startedAt));
    const update = () =>
      setRemaining(Math.max(0, SESSION_MS - (Date.now() - startedAt)));
    update();
    const interval = window.setInterval(update, 1000);
    return () => window.clearInterval(interval);
  }, [user]);
  const totalMinutes = Math.ceil(remaining / 60000);
  return user?.visitante
    ? `${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}min`
    : null;
}
