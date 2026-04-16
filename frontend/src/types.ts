export interface EmailRequest {
  intent: string;
  key_facts: string[];
  tone: string;
  strategy: string;
}

export interface EmailResponse {
  email: string;
  model_name: string;
  strategy: string;
  was_revised: boolean;
}

export interface HealthResponse {
  status: string;
  provider: string;
  has_valid_key: boolean;
}

export type Page = "generate" | "evaluate" | "scenarios";

export interface MetricScore {
  metric_name: string;
  score: number;
  details: string;
}

export interface ScenarioResult {
  scenario_id: number;
  intent: string;
  tone: string;
  strategy: string;
  model_name: string;
  generated_email: string;
  scores: MetricScore[];
}

export interface Scenario {
  id: number;
  intent: string;
  key_facts: string[];
  tone: string;
  reference_email: string;
}

export type EvalEvent =
  | { type: "init"; total: number; scenarios: number; strategies: string[] }
  | { type: "result"; data: ScenarioResult; completed: number; total: number }
  | { type: "error"; scenario_id: number; strategy: string; error: string; completed: number; total: number }
  | { type: "complete"; summary: Record<string, Record<string, number>>; total_results: number };
