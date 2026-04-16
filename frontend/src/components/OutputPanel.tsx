import { useState } from "react";
import {
  Copy,
  Check,
  RefreshCw,
  ExternalLink,
  Mail,
  Sparkles,
  Zap,
  CheckCircle2,
} from "lucide-react";
import type { EmailResponse } from "../types";

interface Props {
  result: EmailResponse | null;
  loading: boolean;
  error: string | null;
  onRegenerate: () => void;
}

function parseEmail(raw: string) {
  const lines = raw.trim().split("\n");
  let subject = "";
  let bodyStart = 0;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].toLowerCase().startsWith("subject:")) {
      subject = lines[i].split(":").slice(1).join(":").trim();
      bodyStart = i + 1;
      break;
    }
  }
  return { subject, body: lines.slice(bodyStart).join("\n").trim() };
}

function Skeleton() {
  return (
    <div className="space-y-5 p-8">
      <div className="skeleton h-5 w-3/4" />
      <div className="h-px bg-white/[0.04]" />
      <div className="space-y-2.5">
        <div className="skeleton h-3.5 w-1/3" />
        <div className="skeleton h-3.5 w-full" />
        <div className="skeleton h-3.5 w-full" />
        <div className="skeleton h-3.5 w-5/6" />
      </div>
      <div className="space-y-2.5 pt-1">
        <div className="skeleton h-3.5 w-full" />
        <div className="skeleton h-3.5 w-4/5" />
        <div className="skeleton h-3.5 w-full" />
        <div className="skeleton h-3.5 w-3/4" />
      </div>
      <div className="space-y-2.5 pt-1">
        <div className="skeleton h-3.5 w-2/5" />
        <div className="skeleton h-3.5 w-1/4" />
      </div>
    </div>
  );
}

export function OutputPanel({ result, loading, error, onRegenerate }: Props) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.email);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const { subject, body } = result
    ? parseEmail(result.email)
    : { subject: "", body: "" };

  const qs = (s: string) => encodeURIComponent(s);
  const gmailUrl = `https://mail.google.com/mail/?view=cm&su=${qs(subject)}&body=${qs(body)}`;
  const outlookUrl = `https://outlook.live.com/mail/0/deeplink/compose?subject=${qs(subject)}&body=${qs(body)}`;

  const actionBtn =
    "flex items-center gap-1.5 px-3 py-[7px] rounded-lg text-[11px] font-semibold " +
    "bg-white/[0.03] text-gray-400 border border-white/[0.06] " +
    "hover:bg-white/[0.06] hover:text-gray-200 transition-all duration-150";

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-[#0B0F14]">
      <div className="p-8 max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-[22px] font-bold text-gray-100 tracking-tight">
              Preview
            </h2>
            <p className="text-[13px] text-gray-500 mt-0.5">
              Generated email output
            </p>
          </div>
          {result && !loading && (
            <div className="flex items-center gap-1.5">
              <button onClick={copy} className={actionBtn}>
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                {copied ? "Copied" : "Copy"}
              </button>
              <button onClick={onRegenerate} className={actionBtn}>
                <RefreshCw className="w-3.5 h-3.5" />
                Regenerate
              </button>
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 px-5 py-4 rounded-xl bg-red-500/[0.08] border border-red-500/20">
            <p className="text-sm text-red-400 font-medium">{error}</p>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="bg-[#111827]/60 border border-white/[0.06] rounded-2xl overflow-hidden">
            <Skeleton />
          </div>
        )}

        {/* Empty state */}
        {!result && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-5">
              <Mail className="w-7 h-7 text-gray-700" />
            </div>
            <h3 className="text-base font-semibold text-gray-400 mb-2">
              No email generated yet
            </h3>
            <p className="text-sm text-gray-600 max-w-xs leading-relaxed">
              Fill in the form on the left and click{" "}
              <span className="text-indigo-400 font-medium">Generate</span> to
              craft your email.
            </p>
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div className="space-y-4">
            {/* Badges */}
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={[
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider",
                  result.strategy === "advanced"
                    ? "bg-indigo-500/[0.1] text-indigo-400"
                    : "bg-amber-500/[0.1] text-amber-400",
                ].join(" ")}
              >
                {result.strategy === "advanced" ? (
                  <Sparkles className="w-3 h-3" />
                ) : (
                  <Zap className="w-3 h-3" />
                )}
                {result.strategy}
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-white/[0.04] text-gray-400 border border-white/[0.06]">
                {result.model_name}
              </span>
              {result.was_revised && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-emerald-500/[0.1] text-emerald-400">
                  <CheckCircle2 className="w-3 h-3" />
                  Revised by critic
                </span>
              )}
            </div>

            {/* Email card */}
            <div className="bg-[#111827]/60 border border-white/[0.06] rounded-2xl overflow-hidden shadow-2xl shadow-black/30 backdrop-blur-sm">
              {/* Subject */}
              <div className="px-7 py-5 border-b border-white/[0.04]">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-600 mb-1.5">
                  Subject
                </div>
                <p className="text-[15px] font-semibold text-gray-100 leading-snug">
                  {subject || "No subject"}
                </p>
              </div>
              {/* Body */}
              <div className="px-7 py-6">
                <div className="text-[14px] text-gray-300 leading-[1.85] whitespace-pre-wrap">
                  {body}
                </div>
              </div>
            </div>

            {/* Send actions */}
            <div className="flex items-center gap-2 pt-1">
              <a
                href={gmailUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[11px] font-semibold bg-red-500/[0.08] text-red-400 border border-red-500/15 hover:bg-red-500/[0.13] transition-all duration-150"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Send via Gmail
              </a>
              <a
                href={outlookUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[11px] font-semibold bg-blue-500/[0.08] text-blue-400 border border-blue-500/15 hover:bg-blue-500/[0.13] transition-all duration-150"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Send via Outlook
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
