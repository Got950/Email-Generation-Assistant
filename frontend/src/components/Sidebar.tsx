import { Mail, BarChart3, FileText, Zap, Circle } from "lucide-react";
import type { HealthResponse, Page } from "../types";

const nav: { id: Page; label: string; icon: typeof Mail }[] = [
  { id: "generate", label: "Generate", icon: Mail },
  { id: "evaluate", label: "Evaluation", icon: BarChart3 },
  { id: "scenarios", label: "Scenarios", icon: FileText },
];

interface Props {
  currentPage: Page;
  onNavigate: (p: Page) => void;
  health: HealthResponse | null;
}

export function Sidebar({ currentPage, onNavigate, health }: Props) {
  const connected = health?.has_valid_key ?? false;

  return (
    <aside className="w-[232px] flex-shrink-0 h-screen border-r border-white/[0.06] bg-[#080b11] flex flex-col">
      <div className="px-5 pt-6 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Zap className="w-[18px] h-[18px] text-white" />
          </div>
          <div>
            <div className="text-[13px] font-bold text-gray-100 tracking-tight">
              Email Assistant
            </div>
            <div className="text-[11px] text-gray-600">AI-Powered Platform</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 pt-1">
        <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-gray-600 px-3 mb-2">
          Navigation
        </div>
        <div className="space-y-0.5">
          {nav.map((item) => {
            const active = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={[
                  "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150",
                  active
                    ? "bg-indigo-500/[0.08] text-indigo-400"
                    : "text-gray-500 hover:text-gray-300 hover:bg-white/[0.03]",
                ].join(" ")}
              >
                <item.icon className="w-[15px] h-[15px]" />
                {item.label}
              </button>
            );
          })}
        </div>
      </nav>

      <div className="px-5 py-4 border-t border-white/[0.06]">
        <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-gray-600 mb-3">
          System
        </div>
        <div className="space-y-2.5 text-[11px]">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Status</span>
            <span className="flex items-center gap-1.5">
              <Circle
                className={`w-[7px] h-[7px] fill-current ${connected ? "text-emerald-400" : "text-red-400"}`}
              />
              <span className={connected ? "text-emerald-400 font-medium" : "text-red-400 font-medium"}>
                {connected ? "Connected" : "No API Key"}
              </span>
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Provider</span>
            <span className="text-gray-400 font-medium">
              {health?.provider?.toUpperCase() ?? "\u2014"}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
