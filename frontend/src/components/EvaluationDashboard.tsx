import { useState, useEffect, useRef, useCallback } from "react";
import {
  Play,
  Square,
  Sparkles,
  Zap,
  AlertCircle,
  CheckCircle2,
  RotateCw,
} from "lucide-react";
import { streamEvaluation } from "../lib/api";
import type { ScenarioResult, EvalEvent } from "../types";

function sc(v: number) {
  if (v >= 85) return "text-emerald-400";
  if (v >= 70) return "text-yellow-400";
  if (v >= 50) return "text-orange-400";
  return "text-red-400";
}

function scBg(v: number) {
  if (v >= 85) return "bg-emerald-500/10";
  if (v >= 70) return "bg-yellow-500/10";
  if (v >= 50) return "bg-orange-500/10";
  return "bg-red-500/10";
}

function scBar(v: number) {
  if (v >= 85) return "bg-emerald-500";
  if (v >= 70) return "bg-yellow-500";
  if (v >= 50) return "bg-orange-500";
  return "bg-red-500";
}

function ScorePill({ value }: { value: number }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold tabular-nums ${sc(value)} ${scBg(value)}`}
    >
      {value.toFixed(0)}
    </span>
  );
}

function MetricBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-[130px] text-[12px] text-gray-400 font-medium truncate">
        {label}
      </span>
      <div className="flex-1 h-[5px] bg-white/[0.04] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${scBar(value)}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className={`w-8 text-right text-[12px] font-bold tabular-nums ${sc(value)}`}>
        {value.toFixed(0)}
      </span>
    </div>
  );
}

function SummaryCard({
  title,
  strategy,
  metrics,
}: {
  title: string;
  strategy: string;
  metrics: Record<string, number>;
}) {
  const overall = metrics["overall_average"] ?? 0;
  const metricEntries = Object.entries(metrics).filter(
    ([k]) => k !== "overall_average"
  );

  return (
    <div className="bg-[#111827]/60 border border-white/[0.06] rounded-2xl p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          {strategy === "advanced" ? (
            <Sparkles className="w-4 h-4 text-indigo-400" />
          ) : (
            <Zap className="w-4 h-4 text-amber-400" />
          )}
          <span className="text-[13px] font-semibold text-gray-200">
            {title}
          </span>
        </div>
        <div className={`text-2xl font-extrabold tabular-nums ${sc(overall)}`}>
          {overall.toFixed(1)}
        </div>
      </div>
      <div className="space-y-3">
        {metricEntries.map(([name, val]) => (
          <MetricBar key={name} label={name} value={val} />
        ))}
      </div>
    </div>
  );
}

export function EvaluationDashboard({ active }: { active?: boolean }) {
  const [results, setResults] = useState<ScenarioResult[]>([]);
  const [errors, setErrors] = useState<number>(0);
  const [summary, setSummary] = useState<Record<string, Record<string, number>> | null>(null);
  const [running, setRunning] = useState(false);
  const [completed, setCompleted] = useState(0);
  const [total, setTotal] = useState(0);
  const [startTime, setStartTime] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const autoStarted = useRef(false);

  const liveSummary = useCallback((): Record<string, Record<string, number>> => {
    if (summary) return summary;
    if (results.length === 0) return {};

    const map: Record<string, Record<string, number[]>> = {};
    for (const r of results) {
      if (!map[r.strategy]) map[r.strategy] = {};
      for (const s of r.scores) {
        if (!map[r.strategy][s.metric_name]) map[r.strategy][s.metric_name] = [];
        map[r.strategy][s.metric_name].push(s.score);
      }
    }

    const out: Record<string, Record<string, number>> = {};
    for (const [strat, metrics] of Object.entries(map)) {
      out[strat] = {};
      const allScores: number[] = [];
      for (const [name, vals] of Object.entries(metrics)) {
        const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
        out[strat][name] = Math.round(avg * 10) / 10;
        allScores.push(...vals);
      }
      out[strat]["overall_average"] =
        Math.round((allScores.reduce((a, b) => a + b, 0) / allScores.length) * 10) / 10;
    }
    return out;
  }, [results, summary]);

  const runEvaluation = useCallback(async () => {
    const controller = new AbortController();
    abortRef.current = controller;

    setRunning(true);
    setResults([]);
    setErrors(0);
    setSummary(null);
    setCompleted(0);
    setTotal(0);
    setStartTime(Date.now());

    try {
      await streamEvaluation(
        ["advanced", "baseline"],
        (event: EvalEvent) => {
          switch (event.type) {
            case "init":
              setTotal(event.total);
              break;
            case "result":
              setResults((prev) => [...prev, event.data]);
              setCompleted(event.completed);
              break;
            case "error":
              setErrors((prev) => prev + 1);
              setCompleted(event.completed);
              break;
            case "complete":
              setSummary(event.summary);
              break;
          }
        },
        controller.signal
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        console.error("Evaluation failed:", err);
      }
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }, []);

  const stopEvaluation = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  useEffect(() => {
    if (active && !autoStarted.current) {
      autoStarted.current = true;
      runEvaluation();
    }
  }, [active, runEvaluation]);

  const elapsed = running ? (Date.now() - startTime) / 1000 : 0;
  const perItem = completed > 0 ? elapsed / completed : 0;
  const eta = completed > 0 ? Math.round(perItem * (total - completed)) : 0;
  const progress = total > 0 ? completed / total : 0;
  const displaySummary = liveSummary();
  const strategies = Object.keys(displaySummary);
  const done = !running && results.length > 0;

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-[#0B0F14]">
      <div className="max-w-5xl mx-auto p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-[22px] font-bold text-gray-100 tracking-tight">
              Evaluation Dashboard
            </h1>
            <p className="text-[13px] text-gray-500 mt-1">
              {done
                ? `${results.length} results across ${strategies.length} strategies`
                : running
                ? "Running evaluation pipeline\u2026"
                : "Evaluate Advanced vs Baseline across 10 scenarios"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {running ? (
              <button
                onClick={stopEvaluation}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-[12px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/15 transition-all duration-150"
              >
                <Square className="w-3.5 h-3.5" />
                Stop
              </button>
            ) : (
              <button
                onClick={runEvaluation}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-[12px] font-semibold bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-500/15 hover:from-indigo-500 hover:to-violet-500 active:scale-[0.98] transition-all duration-200"
              >
                {done ? <RotateCw className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                {done ? "Re-run" : "Run Evaluation"}
              </button>
            )}
          </div>
        </div>

        {running && total > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[12px] text-gray-400 font-medium">
                {completed} / {total} scenarios
              </span>
              <span className="text-[12px] text-gray-500 tabular-nums">
                ~{eta}s remaining
              </span>
            </div>
            <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
          </div>
        )}

        {strategies.length > 0 && (
          <div className={`grid gap-4 mb-8 ${strategies.length >= 2 ? "grid-cols-2" : "grid-cols-1"}`}>
            {strategies.map((strat) => (
              <SummaryCard
                key={strat}
                title={strat.charAt(0).toUpperCase() + strat.slice(1)}
                strategy={strat}
                metrics={displaySummary[strat]}
              />
            ))}
          </div>
        )}

        {(results.length > 0 || errors > 0) && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[11px] font-semibold uppercase tracking-[0.1em] text-gray-500">
                Scenario Results
              </h2>
              {errors > 0 && (
                <span className="text-[11px] font-medium text-red-400">
                  {errors} error{errors !== 1 ? "s" : ""}
                </span>
              )}
            </div>
            <div className="space-y-1.5">
              {results.map((r, i) => {
                const avg =
                  r.scores.reduce((a, s) => a + s.score, 0) / r.scores.length;
                return (
                  <div
                    key={i}
                    className="flex items-center gap-3 px-4 py-3 bg-[#111827]/40 border border-white/[0.04] rounded-xl hover:bg-[#111827]/60 transition-colors duration-150"
                  >
                    <div
                      className={`w-2 h-2 rounded-full flex-shrink-0 ${scBar(avg)}`}
                    />
                    <span
                      className={[
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wide flex-shrink-0",
                        r.strategy === "advanced"
                          ? "bg-indigo-500/10 text-indigo-400"
                          : "bg-amber-500/10 text-amber-400",
                      ].join(" ")}
                    >
                      {r.strategy === "advanced" ? (
                        <Sparkles className="w-2.5 h-2.5" />
                      ) : (
                        <Zap className="w-2.5 h-2.5" />
                      )}
                      {r.strategy}
                    </span>
                    <span className="text-[12px] text-gray-300 truncate flex-1 min-w-0">
                      {r.intent}
                    </span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {r.scores.map((s) => (
                        <ScorePill key={s.metric_name} value={s.score} />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {done && (
          <div className="mt-6 flex items-center gap-2 px-4 py-3 bg-emerald-500/[0.06] border border-emerald-500/15 rounded-xl">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span className="text-[12px] text-emerald-400 font-medium">
              Evaluation complete &mdash; {results.length} results
              {errors > 0 ? `, ${errors} errors` : ""}
            </span>
          </div>
        )}

        {!running && results.length === 0 && !done && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-4">
              <AlertCircle className="w-6 h-6 text-gray-700" />
            </div>
            <h3 className="text-base font-semibold text-gray-400">
              Evaluation will start automatically
            </h3>
            <p className="text-sm text-gray-600 mt-1 max-w-xs leading-relaxed">
              Evaluating 10 scenarios across both strategies with 3 metrics each.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
