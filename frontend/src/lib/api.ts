import type { EmailRequest, EmailResponse, HealthResponse, EvalEvent, Scenario } from "../types";

const API = "http://localhost:8000";

export async function generateEmail(req: EmailRequest): Promise<EmailResponse> {
  const res = await fetch(`${API}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Generation failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API}/health`);
  if (!res.ok) throw new Error("API unavailable");
  return res.json();
}

export async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${API}/scenarios`);
  if (!res.ok) throw new Error("Failed to load scenarios");
  return res.json();
}

export async function streamEvaluation(
  strategies: string[],
  onEvent: (event: EvalEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API}/evaluate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ strategies }),
    signal,
  });

  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => ({ detail: "Evaluation failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const line = part.trim();
      if (line.startsWith("data: ")) {
        try {
          onEvent(JSON.parse(line.slice(6)));
        } catch { /* skip malformed */ }
      }
    }
  }
}
