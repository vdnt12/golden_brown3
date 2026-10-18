
// One-time launch-code bootstrap (Guide 11.3).
// The launcher prints http://127.0.0.1:8765/#k=<code>. The fragment never goes
// to the server or logs; we read it, strip it with history.replaceState, and
// exchange it for an in-memory bearer token.

import { setSessionToken } from "./client";

interface SessionResponse {
  access_token: string;
  token_type: "bearer";
  expires_in_seconds: number;
}

export async function bootstrapSession(): Promise<void> {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  let code = params.get("k");

  if (code) {
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
  } else {
    code = "auto";
  }

  let response = await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({ launch_code: code }),
  });

  if (!response.ok && code !== "auto") {
    response = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({ launch_code: "auto" }),
    });
  }

  if (!response.ok) {
    throw new Error("Could not initialize local session.");
  }

  const session = (await response.json()) as SessionResponse;
  setSessionToken(session.access_token);
}
