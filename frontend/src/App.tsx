import { useState, useEffect, useCallback } from "react";
import { Sidebar } from "./components/Sidebar";
import { InputPanel } from "./components/InputPanel";
import { OutputPanel } from "./components/OutputPanel";
import { EvaluationDashboard } from "./components/EvaluationDashboard";
import { ScenariosList } from "./components/ScenariosList";
import { generateEmail, checkHealth } from "./lib/api";
import type { EmailResponse, HealthResponse, Page } from "./types";

interface LastRequest {
  intent: string;
  keyFacts: string[];
  tone: string;
  strategy: string;
}

export default function App() {
  const [page, setPage] = useState<Page>("generate");
  const [result, setResult] = useState<EmailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [lastRequest, setLastRequest] = useState<LastRequest | null>(null);

  useEffect(() => {
    checkHealth().then(setHealth).catch(() => setHealth(null));
    const id = setInterval(() => {
      checkHealth().then(setHealth).catch(() => setHealth(null));
    }, 30_000);
    return () => clearInterval(id);
  }, []);

  const handleGenerate = useCallback(
    async (intent: string, keyFacts: string[], tone: string, strategy: string) => {
      setLoading(true);
      setError(null);
      setLastRequest({ intent, keyFacts, tone, strategy });
      try {
        const res = await generateEmail({ intent, key_facts: keyFacts, tone, strategy });
        setResult(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Generation failed");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleRegenerate = useCallback(() => {
    if (lastRequest) {
      handleGenerate(lastRequest.intent, lastRequest.keyFacts, lastRequest.tone, lastRequest.strategy);
    }
  }, [lastRequest, handleGenerate]);

  return (
    <div className="flex h-screen overflow-hidden bg-[#0B0F14]">
      <Sidebar currentPage={page} onNavigate={setPage} health={health} />

      <div className="flex flex-1 min-w-0" style={{ display: page === "generate" ? "flex" : "none" }}>
        <InputPanel onGenerate={handleGenerate} loading={loading} />
        <OutputPanel
          result={result}
          loading={loading}
          error={error}
          onRegenerate={handleRegenerate}
        />
      </div>

      <div style={{ display: page === "evaluate" ? "contents" : "none" }}>
        <EvaluationDashboard active={page === "evaluate"} />
      </div>

      <div style={{ display: page === "scenarios" ? "contents" : "none" }}>
        <ScenariosList />
      </div>
    </div>
  );
}
