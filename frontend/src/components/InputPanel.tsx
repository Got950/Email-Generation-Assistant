import { useState, useEffect } from "react";
import {
  MessageSquare,
  List,
  Sparkles,
  Loader2,
  Zap,
  Info,
  Briefcase,
  Building2,
  Coffee,
  Heart,
  Target,
  AlertCircle,
  Smile,
  Flame,
} from "lucide-react";

const tones = [
  { value: "formal", label: "Formal", icon: Briefcase },
  { value: "professional", label: "Professional", icon: Building2 },
  { value: "friendly-casual", label: "Casual", icon: Coffee },
  { value: "empathetic", label: "Empathetic", icon: Heart },
  { value: "persuasive", label: "Persuasive", icon: Target },
  { value: "urgent", label: "Urgent", icon: AlertCircle },
  { value: "warm-grateful", label: "Grateful", icon: Smile },
  { value: "excited", label: "Excited", icon: Flame },
];

interface Props {
  onGenerate: (intent: string, keyFacts: string[], tone: string, strategy: string) => void;
  loading: boolean;
}

export function InputPanel({ onGenerate, loading }: Props) {
  const [intent, setIntent] = useState("");
  const [factsText, setFactsText] = useState("");
  const [tone, setTone] = useState("professional");
  const [strategy, setStrategy] = useState<"advanced" | "baseline">("advanced");

  const facts = factsText
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const canSubmit = intent.trim().length >= 5 && facts.length > 0 && !loading;

  const submit = () => {
    if (canSubmit) onGenerate(intent.trim(), facts, tone, strategy);
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        submit();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  const inputBase =
    "w-full bg-[#0f1419] border border-white/[0.06] rounded-xl text-sm text-gray-200 placeholder-gray-600 " +
    "focus:outline-none focus:ring-2 focus:ring-indigo-500/25 focus:border-indigo-500/40 transition-all duration-200";

  return (
    <div className="w-[460px] flex-shrink-0 border-r border-white/[0.06] h-screen overflow-y-auto bg-[#0B0F14]">
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-[22px] font-bold text-gray-100 tracking-tight">
            Compose Email
          </h1>
          <p className="text-[13px] text-gray-500 mt-1.5 leading-relaxed">
            Define your intent and let AI craft the perfect email.
          </p>
        </div>

        <div className="space-y-6">
          {/* Intent */}
          <fieldset>
            <label className="text-[11px] font-semibold uppercase tracking-[0.08em] text-gray-500 mb-2 block">
              Intent
            </label>
            <div className="relative">
              <MessageSquare className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600 pointer-events-none" />
              <input
                type="text"
                value={intent}
                onChange={(e) => setIntent(e.target.value)}
                placeholder="Follow up after a product demo call"
                className={`${inputBase} pl-10 pr-4 py-3`}
              />
            </div>
            <p className="text-[11px] text-gray-600 mt-1.5 pl-0.5">
              Describe the core purpose of your email
            </p>
          </fieldset>

          {/* Key Facts */}
          <fieldset>
            <div className="flex items-center justify-between mb-2">
              <label className="text-[11px] font-semibold uppercase tracking-[0.08em] text-gray-500">
                Key Facts
              </label>
              <span className="text-[11px] tabular-nums text-gray-600">
                {facts.length} {facts.length === 1 ? "fact" : "facts"}
              </span>
            </div>
            <div className="relative">
              <List className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-600 pointer-events-none" />
              <textarea
                value={factsText}
                onChange={(e) => setFactsText(e.target.value)}
                placeholder={"Demo was held last Tuesday\nClient liked the reporting feature\nNext step is a pilot program"}
                rows={5}
                className={`${inputBase} pl-10 pr-4 py-3 resize-none`}
              />
            </div>
            <p className="text-[11px] text-gray-600 mt-1.5 pl-0.5">
              Enter one fact per line &mdash; all will be included in the email
            </p>
          </fieldset>

          {/* Tone */}
          <fieldset>
            <label className="text-[11px] font-semibold uppercase tracking-[0.08em] text-gray-500 mb-2.5 block">
              Tone
            </label>
            <div className="grid grid-cols-4 gap-1.5">
              {tones.map((t) => {
                const active = tone === t.value;
                return (
                  <button
                    key={t.value}
                    onClick={() => setTone(t.value)}
                    className={[
                      "flex items-center gap-1.5 px-2 py-[9px] rounded-lg text-[11px] font-semibold transition-all duration-150",
                      active
                        ? "bg-indigo-500/[0.12] text-indigo-400 ring-1 ring-inset ring-indigo-500/25"
                        : "bg-white/[0.02] text-gray-500 hover:text-gray-400 hover:bg-white/[0.04]",
                    ].join(" ")}
                  >
                    <t.icon className="w-3.5 h-3.5 flex-shrink-0" />
                    {t.label}
                  </button>
                );
              })}
            </div>
          </fieldset>

          {/* Strategy */}
          <fieldset>
            <div className="flex items-center gap-2 mb-2.5">
              <label className="text-[11px] font-semibold uppercase tracking-[0.08em] text-gray-500">
                Strategy
              </label>
              <div className="group relative">
                <Info className="w-3.5 h-3.5 text-gray-600 cursor-help" />
                <div className="pointer-events-none absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 p-3 bg-gray-800 border border-gray-700/50 rounded-xl text-[11px] text-gray-300 leading-relaxed shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <p className="font-semibold text-gray-200 mb-1">Advanced</p>
                  <p>CoT + Few-Shot + Role-Play with self-reflection critic loop.</p>
                  <p className="font-semibold text-gray-200 mt-2 mb-1">Basic</p>
                  <p>Simple zero-shot prompt — faster but less polished.</p>
                </div>
              </div>
            </div>
            <div className="flex bg-[#0f1419] border border-white/[0.06] rounded-xl p-1">
              <button
                onClick={() => setStrategy("advanced")}
                className={[
                  "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[12px] font-semibold transition-all duration-200",
                  strategy === "advanced"
                    ? "bg-indigo-500/[0.12] text-indigo-400 shadow-sm"
                    : "text-gray-500 hover:text-gray-400",
                ].join(" ")}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Advanced
              </button>
              <button
                onClick={() => setStrategy("baseline")}
                className={[
                  "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[12px] font-semibold transition-all duration-200",
                  strategy === "baseline"
                    ? "bg-indigo-500/[0.12] text-indigo-400 shadow-sm"
                    : "text-gray-500 hover:text-gray-400",
                ].join(" ")}
              >
                <Zap className="w-3.5 h-3.5" />
                Basic
              </button>
            </div>
          </fieldset>

          {/* Generate */}
          <button
            onClick={submit}
            disabled={!canSubmit}
            className={[
              "w-full flex items-center justify-center gap-2.5 py-3.5 rounded-xl text-[13px] font-semibold",
              "bg-gradient-to-r from-indigo-600 to-violet-600 text-white",
              "hover:from-indigo-500 hover:to-violet-500",
              "disabled:opacity-30 disabled:cursor-not-allowed",
              "shadow-lg shadow-indigo-500/15 hover:shadow-indigo-500/25",
              "active:scale-[0.98] transition-all duration-200",
            ].join(" ")}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating&hellip;
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Email
              </>
            )}
          </button>

          <p className="text-center text-[11px] text-gray-600">
            <kbd className="px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] text-[10px] font-mono">
              Ctrl
            </kbd>
            {" + "}
            <kbd className="px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] text-[10px] font-mono">
              Enter
            </kbd>
            {" to generate"}
          </p>
        </div>
      </div>
    </div>
  );
}
