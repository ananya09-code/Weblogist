export type Confidence = "high" | "medium" | "low";

export type TechEvidence = {
  source_type: string;
  source: string;
  signature: string;
  explanation: string;
  weight: number;
  family: string;
};

export type TechItem = {
  name: string;
  confidence: Confidence;
  /** Heuristic evidence score in the existing API range of 0–1. */
  score: number;
  /** Legacy human-readable evidence retained for older clients. */
  evidence: string[];
  evidence_items?: TechEvidence[];
};

export type TechStack = {
  frontend: TechItem[];
  backend: TechItem[];
  styling: TechItem[];
  hosting: TechItem[];
  languages: TechItem[];
  server_runtime?: TechItem[];
  tooling?: TechItem[];
  analytics?: TechItem[];
};

export type ApiRoute = { path: string; source_file: string | null; method_guess: string };
export type ScanResult = { tech_stack: TechStack; api_routes: ApiRoute[]; pages?: string[]; seo: Record<string, unknown>; performance: Record<string, number | string> };
export type Scan = { scan_id: string; url: string | null; status: "queued" | "running" | "done" | "failed"; result: ScanResult | null; error: string | null };
