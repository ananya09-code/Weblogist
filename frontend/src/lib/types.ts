export type Confidence = "high" | "medium" | "low";
export type TechItem = { name: string; confidence: Confidence; score: number; evidence: string[] };
export type TechStack = { frontend: TechItem[]; backend: TechItem[]; styling: TechItem[]; hosting: TechItem[]; languages: TechItem[]; tooling?: TechItem[]; analytics?: TechItem[] };
export type ApiRoute = { path: string; source_file: string | null; method_guess: string };
export type ScanResult = { tech_stack: TechStack; api_routes: ApiRoute[]; pages: string[]; seo: Record<string, unknown>; performance: Record<string, number | string> };
export type Scan = { scan_id: string; url: string | null; status: "queued" | "running" | "done" | "failed"; result: ScanResult | null; error: string | null };
