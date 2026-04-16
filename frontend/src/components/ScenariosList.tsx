import { useState, useEffect } from "react";
import {
  ChevronDown,
  ChevronUp,
  Briefcase,
  Coffee,
  Heart,
  Target,
  AlertCircle,
  Smile,
  Flame,
  Building2,
  Sparkles,
  MessageSquare,
  Loader2,
} from "lucide-react";
import { fetchScenarios } from "../lib/api";
import type { Scenario } from "../types";

const TONE_CONFIG: Record<string, { icon: typeof Briefcase; color: string; bg: string }> = {
  formal:            { icon: Briefcase,  color: "text-blue-400",    bg: "bg-blue-500/10" },
  professional:      { icon: Building2,  color: "text-slate-400",   bg: "bg-slate-500/10" },
  "friendly-casual": { icon: Coffee,     color: "text-amber-400",   bg: "bg-amber-500/10" },
  empathetic:        { icon: Heart,      color: "text-pink-400",    bg: "bg-pink-500/10" },
  excited:           { icon: Sparkles,   color: "text-yellow-400",  bg: "bg-yellow-500/10" },
  neutral:           { icon: MessageSquare, color: "text-gray-400", bg: "bg-gray-500/10" },
  persuasive:        { icon: Target,     color: "text-violet-400",  bg: "bg-violet-500/10" },
  "warm-grateful":   { icon: Smile,      color: "text-orange-400",  bg: "bg-orange-500/10" },
  urgent:            { icon: AlertCircle, color: "text-red-400",    bg: "bg-red-500/10" },
  "casual-compelling": { icon: Flame,    color: "text-emerald-400", bg: "bg-emerald-500/10" },
};

function ToneBadge({ tone }: { tone: string }) {
  const cfg = TONE_CONFIG[tone] || { icon: MessageSquare, color: "text-gray-400", bg: "bg-gray-500/10" };
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wide ${cfg.color} ${cfg.bg}`}>
      <Icon className="w-3 h-3" />
      {tone}
    </span>
  );
}

function ScenarioCard({ scenario }: { scenario: Scenario }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-[#111827]/60 border border-white/[0.06] rounded-2xl overflow-hidden hover:border-white/[0.1] transition-colors duration-200">
      <div className="p-5">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex items-center gap-3 min-w-0">
            <span className="flex-shrink-0 w-7 h-7 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-[11px] font-bold text-gray-500 tabular-nums">
              {scenario.id}
            </span>
            <h3 className="text-[14px] font-semibold text-gray-200 leading-snug truncate">
              {scenario.intent}
            </h3>
          </div>
          <ToneBadge tone={scenario.tone} />
        </div>

        <div className="ml-10">
          <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-gray-600 mb-2">
            Key Facts
          </p>
          <ul className="space-y-1.5">
            {scenario.key_facts.map((fact, i) => (
              <li key={i} className="flex items-start gap-2 text-[12px] text-gray-400 leading-relaxed">
                <span className="mt-1.5 w-1 h-1 rounded-full bg-gray-600 flex-shrink-0" />
                {fact}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {scenario.reference_email && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between px-5 py-2.5 bg-white/[0.015] border-t border-white/[0.04] hover:bg-white/[0.03] transition-colors duration-150"
          >
            <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-gray-500">
              Reference Email
            </span>
            {expanded ? (
              <ChevronUp className="w-3.5 h-3.5 text-gray-600" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
            )}
          </button>

          {expanded && (
            <div className="px-5 pb-5 pt-3 border-t border-white/[0.04]">
              <pre className="text-[12px] text-gray-400 leading-relaxed whitespace-pre-wrap font-sans">
                {scenario.reference_email}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function ScenariosList() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-[#0B0F14]">
      <div className="max-w-4xl mx-auto p-8">
        <div className="mb-8">
          <h1 className="text-[22px] font-bold text-gray-100 tracking-tight">
            Test Scenarios
          </h1>
          <p className="text-[13px] text-gray-500 mt-1">
            {scenarios.length > 0
              ? `${scenarios.length} scenarios with hand-crafted reference emails for benchmarking`
              : "Loading scenarios from data/scenarios.json\u2026"}
          </p>
        </div>

        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-6 h-6 text-gray-600 animate-spin mb-3" />
            <span className="text-[13px] text-gray-500">Loading scenarios\u2026</span>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 px-4 py-3 bg-red-500/[0.06] border border-red-500/15 rounded-xl">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span className="text-[12px] text-red-400 font-medium">{error}</span>
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-3">
            {scenarios.map((s) => (
              <ScenarioCard key={s.id} scenario={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
