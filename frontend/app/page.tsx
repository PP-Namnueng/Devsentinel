"use client";

import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronDown,
  Database,
  ExternalLink,
  FileCode2,
  Flame,
  GitPullRequest,
  KeyRound,
  Layers3,
  Loader2,
  Network,
  Plug,
  Play,
  Save,
  Server,
  Settings,
  ShieldAlert,
  SlidersHorizontal,
  TerminalSquare
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

const API_ORIGIN = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8010").replace(/\/$/, "");
const RUNTIME_API_BASE = API_ORIGIN.endsWith("/api") ? API_ORIGIN.slice(0, -4) : API_ORIGIN;
const API_BASE = `${RUNTIME_API_BASE}/api`;
const SHOW_DEBUG_MARKDOWN = process.env.NEXT_PUBLIC_SHOW_DEBUG_MARKDOWN === "true";

const SAMPLE_PR = `diff --git a/backend/app/api/users.py b/backend/app/api/users.py
index 45f2abc..77e83bc 100644
--- a/backend/app/api/users.py
+++ b/backend/app/api/users.py
@@ -1,14 +1,35 @@
 from fastapi import APIRouter, Depends
 from sqlalchemy.orm import Session
 
 from app.db import get_db
+from app.services.email import send_welcome_email
 
 router = APIRouter()
 
 
+ADMIN_PASSWORD = "Summer2026!"
+
+
 @router.get("/users/search")
 def search_users(q: str, db: Session = Depends(get_db)):
-    return db.execute(
-        "select id, email, role from users where email = :email",
-        {"email": q},
-    ).fetchall()
+    sql = f"select id, email, role, password_hash from users where email = '{q}'"
+    return db.execute(sql).fetchall()
+
+
+@router.post("/users/{user_id}/reset-password")
+def reset_password(user_id: int, db: Session = Depends(get_db)):
+    user = db.execute(
+        f"select id, email from users where id = {user_id}"
+    ).fetchone()
+
+    db.execute(
+        f"update users set password_hash = '{ADMIN_PASSWORD}' where id = {user_id}"
+    )
+    db.commit()
+    send_welcome_email(user.email, ADMIN_PASSWORD)
+    return {"status": "ok"}
+
+
+@router.post("/users/{user_id}/notify")
+def notify_user(user_id: int):
+    from app.integrations.slack_client import SlackClient
+
+    SlackClient().post_message(f"User {user_id} was updated")
+    return {"status": "sent"}`;

const SAMPLE_LOGS = `2026-05-06T09:00:01Z INFO api edge request_rate=240rps route=/dashboard p95_ms=180 status=200
2026-05-06T09:01:14Z INFO api edge request_rate=780rps route=/dashboard p95_ms=410 status=200
2026-05-06T09:02:22Z WARN api dashboard request_id=req-1021 user_id=1842 query_count=312 duration_ms=2800 message="high query count while rendering dashboard"
2026-05-06T09:02:24Z WARN db postgres pool_in_use=18 pool_size=20 wait_ms=1200 message="connection pool nearing exhaustion"
2026-05-06T09:03:05Z WARN api dashboard request_id=req-1044 user_id=1849 query_count=487 duration_ms=5100 message="repeated account and project lookups detected"
2026-05-06T09:03:18Z ERROR db postgres pool_in_use=20 pool_size=20 wait_ms=5000 message="connection checkout timeout"
2026-05-06T09:03:19Z ERROR api dashboard request_id=req-1050 status=503 error="sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 0 reached"
2026-05-06T09:04:03Z ERROR api dashboard request_id=req-1068 status=503 error="dependency timeout while loading dashboard widgets"
2026-05-06T09:05:30Z INFO api edge request_rate=690rps route=/dashboard p95_ms=6200 status=503
2026-05-06T09:07:45Z INFO ops deploy action=rollback version=2026.05.06.1 previous=2026.05.05.4
2026-05-06T09:09:12Z INFO api edge request_rate=310rps route=/dashboard p95_ms=340 status=200`;

const INCIDENT_SCENARIOS = [
  {
    id: "db_saturation_after_deploy",
    label: "DB saturation after deploy",
    service: "dashboard-api",
    severity: "sev2" as const,
    startedAt: "2026-05-06T09:02:00Z"
  },
  {
    id: "cache_outage_causing_db_overload",
    label: "Cache outage causing DB overload",
    service: "checkout-api",
    severity: "sev2" as const,
    startedAt: "2026-05-07T14:18:00Z"
  },
  {
    id: "memory_leak_pod_restart_loop",
    label: "Memory leak restart loop",
    service: "invoice-worker",
    severity: "sev3" as const,
    startedAt: "2026-05-08T02:12:00Z"
  }
];

function scenarioLabel(id: string) {
  return INCIDENT_SCENARIOS.find((scenario) => scenario.id === id)?.label ?? id;
}

type PRIssue = {
  severity: "critical" | "high" | "medium" | "low";
  category: "security" | "bug" | "concurrency" | "performance" | "maintainability" | "architecture" | "operational_risk";
  grounding: "grounded" | "inferred" | "heuristic" | "needs_verification";
  title: string;
  file?: string;
  line?: number;
  end_line?: number;
  evidence: string;
  reasoning: string;
  suggested_fix: string;
  skill_references: string[];
};

type PRResult = {
  decision: "approve" | "request_changes" | "needs_discussion";
  summary: string;
  issues: PRIssue[];
  reviewer_notes: string[];
  runtime?: {
    provider: string;
    runtime_mode: "deterministic_demo" | "llm";
    gateway: string;
    model: string;
    schema_name: string;
    schema_validation_status: "passed";
    latency_ms?: number | null;
    latency_seconds?: number | null;
    grounding_stats?: {
      grounded: number;
      inferred: number;
      heuristic: number;
      needs_verification: number;
    } | null;
  } | null;
};

type GitHubPRReviewResponse = {
  owner: string;
  repo: string;
  pull_number: number;
  model: string;
  review: PRResult;
  comment_body: string;
  posted_to_github: boolean;
  github_comment_url?: string | null;
};

type Grounding = "grounded" | "inferred" | "heuristic";

type IncidentTimelineEvent = {
  timestamp: string;
  service: string;
  event_type: string;
  summary: string;
  grounding: Grounding;
  evidence_refs: string[];
};

type IncidentPreventionAction = {
  priority: "p0" | "p1" | "p2";
  action: string;
  rationale: string;
  related_evidence: string[];
};

type IncidentSymptom = {
  service: string;
  summary: string;
  grounding: Grounding;
  evidence_refs: string[];
};

type RootCauseCandidate = {
  title: string;
  explanation: string;
  grounding: Grounding;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  uncertainty: string;
};

type IncidentResult = {
  incident_title: string;
  executive_summary: string;
  severity_assessment: string;
  affected_services: string[];
  detected_symptoms: IncidentSymptom[];
  timeline: IncidentTimelineEvent[];
  root_cause_candidates: RootCauseCandidate[];
  most_likely_root_cause: RootCauseCandidate;
  blast_radius: string;
  evidence_summary: string;
  contributing_factors: string[];
  prevention_actions: IncidentPreventionAction[];
  follow_up_questions: string[];
  postmortem_markdown: string;
  grounding_notes: string;
  analysis_limitations: string[];
  runtime?: {
    provider: string;
    runtime_mode: "deterministic_demo" | "llm";
    gateway: string;
    model: string;
    source_provider: string;
    schema_name: string;
    schema_validation_status: "passed";
    latency_ms?: number | null;
    latency_seconds?: number | null;
    evidence_counts: {
      logs: number;
      metrics: number;
      deployments: number;
      traces: number;
    };
  };
};

type StoredIncident = {
  id: string;
  created_at: string;
  source: string;
  alert_id: string;
  alert_name: string;
  service: string;
  environment: string;
  severity: "sev1" | "sev2" | "sev3" | "sev4";
  status: "completed";
  report: IncidentResult;
  labels: Record<string, string>;
};

type LoadingMode = "pr" | "github" | "incident";
type AppView = "workspace" | "settings";
type Provider = "OpenAI" | "Ollama" | "OpenRouter" | "Custom Endpoint";
type IncidentEvidenceProvider = "fixture" | "local_file" | "datadog" | "loki_prometheus";

type RuntimeModelsResponse = {
  provider: string;
  models: string[];
};

type EvidenceConnectionTestResult = {
  provider: string;
  ok: boolean;
  checks: Array<{
    name: string;
    ok: boolean;
    detail: string;
  }>;
};

type RoutingCandidateModel = {
  id: string;
  provider: string;
  model: string;
  label: string;
};

type SavedGatewayConfig = {
  provider: Provider;
  model: string;
  baseUrl: string;
  apiKey: string;
  temperature: number;
  maxTokens: number;
  routingCandidates: RoutingCandidateModel[];
  taskRouting: Record<string, string>;
  incidentEvidence: IncidentEvidenceSettings;
};

type BackendRuntimeRoute = {
  provider?: string | null;
  model?: string | null;
  label?: string | null;
};

type BackendRuntimeConfig = {
  model_gateway?: BackendRuntimeProviderConfig;
  task_routing: Record<string, BackendRuntimeRoute>;
  incident_evidence?: IncidentEvidenceSettings;
};

type BackendRuntimeProviderConfig = {
  provider: "demo" | "openai_compatible" | "ollama";
  base_url?: string | null;
  model?: string | null;
  api_key?: string | null;
};

type RuntimeConnectionTestResult = {
  provider: string;
  ok: boolean;
  detail: string;
  models: string[];
};

type IncidentEvidenceSettings = {
  provider?: IncidentEvidenceProvider | null;
  log_file_path?: string | null;
  log_limit?: number | null;
  loki_base_url?: string | null;
  prometheus_base_url?: string | null;
  datadog_site?: string | null;
};

type RoutedModel = {
  model: string;
  source: string;
};

const ROUTING_MODELS_STORAGE_KEY = "devsentinel-routing-models";
const GATEWAY_CONFIG_STORAGE_KEY = "devsentinel-gateway-config";
const ACTIVE_RUNTIME_OPTION = "Use Active Runtime";
const DEFAULT_INCIDENT_EVIDENCE_SETTINGS: IncidentEvidenceSettings = {
  provider: "fixture",
  log_file_path: "app/log_sources/dashboard-api.log",
  log_limit: 200,
  loki_base_url: "http://localhost:3100",
  prometheus_base_url: "http://localhost:9090",
  datadog_site: "datadoghq.com"
};

const providerModels: Record<Provider, string[]> = {
  OpenAI: ["gpt-4.1", "gpt-4.1-mini", "o4-mini"],
  Ollama: [],
  OpenRouter: ["anthropic/claude-3.5-sonnet", "qwen/qwen-2.5-coder-32b", "mistralai/codestral"],
  "Custom Endpoint": ["devsentinel-coder-14b", "custom-review-model", "custom-incident-model"]
};

const providerBaseUrls: Record<Provider, string> = {
  OpenAI: "https://api.openai.com/v1",
  Ollama: "http://localhost:11434",
  OpenRouter: "https://openrouter.ai/api/v1",
  "Custom Endpoint": ""
};

function backendProviderFromUi(provider: Provider): BackendRuntimeProviderConfig["provider"] {
  if (provider === "Ollama") return "ollama";
  return "openai_compatible";
}

function uiProviderFromBackend(provider?: string | null, baseUrl?: string | null): Provider {
  if (provider === "ollama") return "Ollama";
  if (baseUrl?.includes("openrouter.ai")) return "OpenRouter";
  if (baseUrl?.includes("api.openai.com")) return "OpenAI";
  return "Custom Endpoint";
}

const INVESTIGATION_STAGES: Record<LoadingMode, string[]> = {
  pr: [
    "Parsing diff...",
    "Analyzing architecture boundaries...",
    "Checking security conventions...",
    "Detecting risky patterns...",
    "Generating validated output..."
  ],
  github: [
    "Fetching GitHub PR diff...",
    "Analyzing architecture boundaries...",
    "Checking security conventions...",
    "Rendering PR comment...",
    "Posting GitHub review..."
  ],
  incident: [
    "Parsing log stream...",
    "Reconstructing incident timeline...",
    "Correlating database symptoms...",
    "Identifying causal chain...",
    "Generating validated post-mortem..."
  ]
};

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function titleCase(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatLocalDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });
}

function severityClass(value: string) {
  if (value === "critical" || value === "sev1" || value === "failure") {
    return "border-red-200/14 bg-red-200/[0.055] text-red-200/90";
  }
  if (value === "high" || value === "sev2" || value === "p0" || value === "warning") {
    return "border-amber-100/14 bg-amber-100/[0.055] text-amber-100/90";
  }
  if (value === "medium" || value === "sev3" || value === "p1" || value === "recovered") {
    return "border-cyan-100/14 bg-cyan-100/[0.052] text-cyan-100/90";
  }
  return "border-slate-200/10 bg-slate-200/[0.04] text-slate-300/90";
}

function timelineTone(summary: string) {
  const text = summary.toLowerCase();
  if (text.includes("503") || text.includes("exhausted") || text.includes("timeout")) return "failure";
  if (text.includes("spike") || text.includes("n+1") || text.includes("nearing")) return "warning";
  if (text.includes("recover") || text.includes("rollback")) return "recovered";
  return "healthy";
}

function groundingClass(value: Grounding) {
  if (value === "grounded") return "border-emerald-100/14 bg-emerald-100/[0.055] text-emerald-100/90";
  if (value === "inferred") return "border-cyan-100/14 bg-cyan-100/[0.052] text-cyan-100/90";
  return "border-amber-100/14 bg-amber-100/[0.055] text-amber-100/90";
}

function toneDotClass(tone: string) {
  if (tone === "failure") return "border-red-200 bg-red-300";
  if (tone === "warning") return "border-amber-100 bg-amber-200";
  if (tone === "recovered") return "border-cyan-100 bg-cyan-200";
  return "border-emerald-100 bg-emerald-300";
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const detail = await response.text();
    let message = detail;
    try {
      const parsed = JSON.parse(detail) as { detail?: unknown };
      if (typeof parsed.detail === "string") {
        message = parsed.detail;
      }
      if (parsed.detail && typeof parsed.detail === "object" && "message" in parsed.detail) {
        message = String((parsed.detail as { message: unknown }).message);
      }
    } catch {
      message = detail;
    }
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function putJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function modelFromSelection(selection?: string) {
  if (!selection || selection === "Active Runtime" || selection === ACTIVE_RUNTIME_OPTION) {
    return null;
  }
  const separator = " / ";
  if (selection.includes(separator)) {
    return selection.split(separator).slice(1).join(separator).trim();
  }
  return selection;
}

function routeFromSelection(selection?: string): BackendRuntimeRoute | null {
  const model = modelFromSelection(selection);
  if (!model) return null;
  const separator = " / ";
  const provider = selection?.includes(separator) ? selection.split(separator)[0].trim() : undefined;
  return {
    provider,
    model,
    label: selection,
  };
}

function modelFromRoutingEntry(entry?: unknown) {
  if (typeof entry === "string") {
    return modelFromSelection(entry);
  }
  if (entry && typeof entry === "object") {
    const candidate = entry as { model?: unknown; label?: unknown };
    if (typeof candidate.model === "string") {
      return modelFromSelection(candidate.model);
    }
    if (typeof candidate.label === "string") {
      return modelFromSelection(candidate.label);
    }
  }
  return null;
}

function getSavedPrReviewModel(): RoutedModel | null {
  if (typeof window === "undefined") return null;
  const backendConfig = window.localStorage.getItem("devsentinel-backend-runtime-config");
  if (backendConfig) {
    try {
      const config = JSON.parse(backendConfig) as BackendRuntimeConfig;
      const route = config.task_routing?.PR_AUTOPILOT;
      if (route?.model) {
        return { model: route.model, source: route.label ? "Backend Runtime Config" : "Backend Runtime Config" };
      }
    } catch {
      window.localStorage.removeItem("devsentinel-backend-runtime-config");
    }
  }
  const savedConfig = window.localStorage.getItem(GATEWAY_CONFIG_STORAGE_KEY);
  if (!savedConfig) return null;
  try {
    const config = JSON.parse(savedConfig) as SavedGatewayConfig;
    const routing = config.taskRouting ?? {};
    const routeCandidates: Array<[string, unknown]> = [
      ["PR_AUTOPILOT", routing.PR_AUTOPILOT],
      ["PR_REVIEW", routing.PR_REVIEW],
      ["PR_AUTOPILOT", routing.prReview],
    ];
    for (const [source, entry] of routeCandidates) {
      const model = modelFromRoutingEntry(entry);
      if (model) {
        return { model, source };
      }
    }
    const fallbackModel = modelFromSelection(config.model);
    return fallbackModel ? { model: fallbackModel, source: "Default Runtime" } : null;
  } catch {
    return null;
  }
}

function getSavedIncidentModel(): RoutedModel | null {
  if (typeof window === "undefined") return null;
  const backendConfig = window.localStorage.getItem("devsentinel-backend-runtime-config");
  if (backendConfig) {
    try {
      const config = JSON.parse(backendConfig) as BackendRuntimeConfig;
      const route = config.task_routing?.INCIDENT_AUTOPSY;
      if (route?.model) {
        return { model: route.model, source: route.label ? "Backend Runtime Config" : "Backend Runtime Config" };
      }
    } catch {
      window.localStorage.removeItem("devsentinel-backend-runtime-config");
    }
  }
  const savedConfig = window.localStorage.getItem(GATEWAY_CONFIG_STORAGE_KEY);
  if (!savedConfig) return null;
  try {
    const config = JSON.parse(savedConfig) as SavedGatewayConfig;
    const routing = config.taskRouting ?? {};
    const routeCandidates: Array<[string, unknown]> = [
      ["INCIDENT_AUTOPSY", routing.INCIDENT_AUTOPSY],
      ["INCIDENT_ANALYSIS", routing.incidentAnalysis],
    ];
    for (const [source, entry] of routeCandidates) {
      const model = modelFromRoutingEntry(entry);
      if (model) {
        return { model, source };
      }
    }
    const fallbackModel = modelFromSelection(config.model);
    return fallbackModel ? { model: fallbackModel, source: "Default Runtime" } : null;
  } catch {
    return null;
  }
}

function backendConfigToSavedConfig(config: BackendRuntimeConfig): Partial<SavedGatewayConfig> {
  const routes = config.task_routing ?? {};
  const gateway = config.model_gateway;
  const gatewayProvider = gateway && gateway.provider !== "demo" ? uiProviderFromBackend(gateway.provider, gateway.base_url) : null;
  return {
    ...(gatewayProvider
      ? {
          provider: gatewayProvider,
          model: gateway?.model ?? ACTIVE_RUNTIME_OPTION,
          baseUrl: gateway?.base_url ?? providerBaseUrls[gatewayProvider],
          apiKey: gateway?.api_key ?? "",
        }
      : {}),
    taskRouting: {
      prReview: routes.PR_AUTOPILOT?.label ?? routes.PR_AUTOPILOT?.model ?? ACTIVE_RUNTIME_OPTION,
      incidentAnalysis: routes.INCIDENT_AUTOPSY?.label ?? routes.INCIDENT_AUTOPSY?.model ?? ACTIVE_RUNTIME_OPTION,
      rootCauseAnalysis: routes.ROOT_CAUSE_ANALYSIS?.label ?? routes.ROOT_CAUSE_ANALYSIS?.model ?? ACTIVE_RUNTIME_OPTION,
    },
    incidentEvidence: {
      ...DEFAULT_INCIDENT_EVIDENCE_SETTINGS,
      ...(config.incident_evidence ?? {})
    },
  };
}

function savedConfigToBackendConfig(config: SavedGatewayConfig): BackendRuntimeConfig {
  const taskRouting: Record<string, BackendRuntimeRoute> = {};
  const prRoute = routeFromSelection(config.taskRouting.prReview);
  const incidentRoute = routeFromSelection(config.taskRouting.incidentAnalysis);
  const rootCauseRoute = routeFromSelection(config.taskRouting.rootCauseAnalysis);
  const defaultRoute = routeFromSelection(config.model);

  if (prRoute ?? defaultRoute) {
    taskRouting.PR_AUTOPILOT = prRoute ?? defaultRoute!;
  }
  if (incidentRoute ?? defaultRoute) {
    taskRouting.INCIDENT_AUTOPSY = incidentRoute ?? defaultRoute!;
  }
  if (rootCauseRoute ?? defaultRoute) {
    taskRouting.ROOT_CAUSE_ANALYSIS = rootCauseRoute ?? defaultRoute!;
  }

  return {
    model_gateway: {
      provider: backendProviderFromUi(config.provider),
      base_url: config.provider === "Ollama" ? providerBaseUrls.Ollama : config.baseUrl,
      model: modelFromSelection(config.model) ?? config.model,
      api_key: config.provider === "Ollama" ? null : config.apiKey
    },
    task_routing: taskRouting,
    incident_evidence: config.incidentEvidence
  };
}

function getSavedIncidentEvidenceSettings(): IncidentEvidenceSettings {
  if (typeof window === "undefined") return DEFAULT_INCIDENT_EVIDENCE_SETTINGS;
  const backendConfig = window.localStorage.getItem("devsentinel-backend-runtime-config");
  if (backendConfig) {
    try {
      const config = JSON.parse(backendConfig) as BackendRuntimeConfig;
      return {
        ...DEFAULT_INCIDENT_EVIDENCE_SETTINGS,
        ...(config.incident_evidence ?? {})
      };
    } catch {
      window.localStorage.removeItem("devsentinel-backend-runtime-config");
    }
  }

  const savedConfig = window.localStorage.getItem(GATEWAY_CONFIG_STORAGE_KEY);
  if (savedConfig) {
    try {
      const config = JSON.parse(savedConfig) as SavedGatewayConfig;
      return {
        ...DEFAULT_INCIDENT_EVIDENCE_SETTINGS,
        ...(config.incidentEvidence ?? {})
      };
    } catch {
      window.localStorage.removeItem(GATEWAY_CONFIG_STORAGE_KEY);
    }
  }
  return DEFAULT_INCIDENT_EVIDENCE_SETTINGS;
}

export default function Home() {
  const [prInput, setPrInput] = useState(SAMPLE_PR);
  const [prResult, setPrResult] = useState<PRResult | null>(null);
  const [incidentEvidenceSource, setIncidentEvidenceSource] = useState<IncidentEvidenceProvider>("fixture");
  const [incidentScenario, setIncidentScenario] = useState("db_saturation_after_deploy");
  const [incidentService, setIncidentService] = useState("dashboard-api");
  const [incidentSeverity, setIncidentSeverity] = useState<"sev1" | "sev2" | "sev3" | "sev4">("sev2");
  const [incidentEnvironment, setIncidentEnvironment] = useState("production");
  const [incidentStartedAt, setIncidentStartedAt] = useState("2026-05-06T09:02:00Z");
  const [incidentWindowMinutes, setIncidentWindowMinutes] = useState("30");
  const [githubOwner, setGithubOwner] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [githubPullNumber, setGithubPullNumber] = useState("");
  const [githubRepositoryContext, setGithubRepositoryContext] = useState("");
  const [githubPostComment, setGithubPostComment] = useState(true);
  const [githubReview, setGithubReview] = useState<GitHubPRReviewResponse | null>(null);
  const [incidentResult, setIncidentResult] = useState<IncidentResult | null>(null);
  const [incidentHistory, setIncidentHistory] = useState<StoredIncident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [incidentHistoryLoaded, setIncidentHistoryLoaded] = useState(false);
  const [loading, setLoading] = useState<LoadingMode | null>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<AppView>("workspace");
  const [backendRuntimeConfig, setBackendRuntimeConfig] = useState<BackendRuntimeConfig | null>(null);

  useEffect(() => {
    if (!loading) {
      setStageIndex(0);
      return;
    }
    const stages = INVESTIGATION_STAGES[loading];
    const interval = window.setInterval(() => {
      setStageIndex((current) => Math.min(current + 1, stages.length - 1));
    }, 560);
    return () => window.clearInterval(interval);
  }, [loading]);

  const routedPrReviewModel = useMemo(() => {
    const route = backendRuntimeConfig?.task_routing?.PR_AUTOPILOT;
    if (route?.model) {
      return { model: route.model, source: route.label ? "Backend Runtime Config" : "Backend Runtime Config" };
    }
    const gatewayModel = backendRuntimeConfig?.model_gateway?.model;
    if (gatewayModel && gatewayModel !== ACTIVE_RUNTIME_OPTION) {
      return { model: gatewayModel, source: "Backend Runtime Config" };
    }
    return getSavedPrReviewModel();
  }, [backendRuntimeConfig, view]);

  async function refreshBackendRuntimeConfig() {
    const config = await getJson<BackendRuntimeConfig>("/runtime-config");
    window.localStorage.setItem("devsentinel-backend-runtime-config", JSON.stringify(config));
    setBackendRuntimeConfig(config);
    return config;
  }

  useEffect(() => {
    const savedEvidence = getSavedIncidentEvidenceSettings();
    if (savedEvidence.provider) {
      setIncidentEvidenceSource(savedEvidence.provider);
    }
  }, [view]);

  useEffect(() => {
    let active = true;

    async function loadInitialIncidents() {
      try {
        await refreshBackendRuntimeConfig();
        const incidents = await getJson<StoredIncident[]>("/incidents");
        if (!active) return;
        setIncidentHistory(incidents);
        setIncidentHistoryLoaded(true);
        if (!incidentResult && incidents[0]) {
          setSelectedIncidentId(incidents[0].id);
          setIncidentResult(incidents[0].report);
        }
      } catch {
        if (active) {
          setIncidentHistoryLoaded(true);
        }
      }
    }

    loadInitialIncidents();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const interval = window.setInterval(async () => {
      try {
        const latest = await getJson<StoredIncident | null>("/incidents/latest");
        if (!latest) return;
        setIncidentHistory((current) => {
          const withoutLatest = current.filter((item) => item.id !== latest.id);
          return [latest, ...withoutLatest].sort((a, b) => b.created_at.localeCompare(a.created_at));
        });
        setSelectedIncidentId((current) => {
          if (current === latest.id) return current;
          setIncidentResult(latest.report);
          return latest.id;
        });
      } catch {
        // Background refresh should not interrupt active analysis workflows.
      }
    }, 5000);

    return () => window.clearInterval(interval);
  }, []);

  async function refreshIncidentHistory(selectLatest = false) {
    const incidents = await getJson<StoredIncident[]>("/incidents");
    setIncidentHistory(incidents);
    if (selectLatest && incidents[0]) {
      setSelectedIncidentId(incidents[0].id);
      setIncidentResult(incidents[0].report);
    }
  }

  function selectIncident(incident: StoredIncident) {
    setSelectedIncidentId(incident.id);
    setIncidentResult(incident.report);
    setError(null);
  }

  async function runPrReview() {
    const selectedModel = getSavedPrReviewModel()?.model;
    if (!selectedModel) {
      setError("Select and save a model in Settings before running PR Autopilot.");
      return;
    }

    setError(null);
    setPrResult(null);
    setLoading("pr");
    try {
      const [result] = await Promise.all([
        postJson<PRResult>("/pr-autopilot", {
          diff: prInput,
          repository_context: "",
          model: selectedModel
        }),
        sleep(2850)
      ]);
      setPrResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PR review failed");
    } finally {
      setLoading(null);
    }
  }

  async function runGithubPrReview() {
    const pullNumber = Number(githubPullNumber);
    const prReviewModel = getSavedPrReviewModel()?.model;
    if (!prReviewModel) {
      setError("No PR review model configured. Please configure PR_AUTOPILOT in Task Routing Settings.");
      return;
    }
    if (!githubOwner.trim() || !githubRepo.trim() || !Number.isInteger(pullNumber) || pullNumber < 1) {
      setError("Enter a GitHub owner, repository, and PR number before running GitHub PR review.");
      return;
    }

    setError(null);
    setGithubReview(null);
    setLoading("github");
    try {
      const [result] = await Promise.all([
        postJson<GitHubPRReviewResponse>("/github/pr-review", {
          owner: githubOwner.trim(),
          repo: githubRepo.trim(),
          pull_number: pullNumber,
          model: prReviewModel,
          repository_context: githubRepositoryContext.trim() || null,
          post_comment: githubPostComment
        }),
        sleep(2850)
      ]);
      setGithubReview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "GitHub PR review failed");
    } finally {
      setLoading(null);
    }
  }

  async function runIncidentAutopsy() {
    const incidentModel = getSavedIncidentModel()?.model;
    const evidenceSettings = getSavedIncidentEvidenceSettings();
    const evidenceProvider = incidentEvidenceSource || evidenceSettings.provider || "fixture";
    setError(null);
    setIncidentResult(null);
    setLoading("incident");
    try {
      const [result] = await Promise.all([
        postJson<IncidentResult>("/incidents/webhook", {
          alert_id: `manual-${incidentScenario}`,
          alert_name: scenarioLabel(incidentScenario),
          service: incidentService,
          environment: incidentEnvironment,
          severity: incidentSeverity,
          started_at: incidentStartedAt,
          window_minutes: Number(incidentWindowMinutes) || 30,
          description: "Incident Autopsy alert trigger from DevSentinel UI.",
          labels: {
            scenario_id: incidentScenario,
            evidence_provider: evidenceProvider,
            ...(evidenceSettings.log_file_path ? { log_file_path: evidenceSettings.log_file_path } : {})
          },
          evidence_provider: evidenceProvider,
          scenario_id: evidenceProvider === "fixture" ? incidentScenario : null,
          model: incidentModel ?? null
        }),
        sleep(2850)
      ]);
      setIncidentResult(result);
      await refreshIncidentHistory(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Incident autopsy failed");
    } finally {
      setLoading(null);
    }
  }

  function loadSamplePr() {
    setPrInput(SAMPLE_PR);
    setPrResult(null);
    setError(null);
    setView("workspace");
  }

  return (
    <main className="min-h-screen text-slate-100">
      <header className="border-b border-white/[0.065] bg-[#101720]/82 shadow-[0_8px_22px_rgba(0,0,0,0.12)]">
        <div className="mx-auto flex max-w-[1500px] flex-col gap-4 px-7 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.075] bg-white/[0.032]">
              <ShieldAlert className="h-5 w-5 text-emerald-100/80" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-normal text-slate-100">DevSentinel</h1>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500/90">AI Engineering Intelligence Platform</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <SystemPill tone="green" label="SYSTEM ONLINE" />
            <SystemPill label="VALIDATED OUTPUTS" />
            <SystemPill label="SKILL.MD MEMORY" />
            <SystemPill tone="cyan" label={`MODEL: ${routedPrReviewModel?.model ?? "Active Runtime"}`} />
            <Button
              size="sm"
              variant={view === "settings" ? "secondary" : "ghost"}
              onClick={() => setView(view === "settings" ? "workspace" : "settings")}
              className="ml-1"
            >
              <Settings className="h-4 w-4" />
              {view === "settings" ? "Workbench" : "Settings"}
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1500px] px-7 py-7">
        {view === "settings" ? (
          <ModelGatewaySettings onLoadSamplePr={loadSamplePr} onRuntimeConfigSaved={setBackendRuntimeConfig} />
        ) : (
          <>
        {error && (
          <div className="mb-4 rounded-xl border border-red-200/14 bg-red-200/[0.055] p-3 text-sm text-red-200/90">
            {error}
          </div>
        )}

        <Tabs defaultValue="pr">
          <div className="mb-5 flex items-center justify-between gap-3">
            <TabsList>
              <TabsTrigger value="pr">
                <GitPullRequest className="mr-2 h-4 w-4" aria-hidden="true" />
                PR Autopilot
              </TabsTrigger>
              <TabsTrigger value="github">
                <Plug className="mr-2 h-4 w-4" aria-hidden="true" />
                GitHub PR Review
              </TabsTrigger>
              <TabsTrigger value="incident">
                <Flame className="mr-2 h-4 w-4" aria-hidden="true" />
                Incident Autopsy
              </TabsTrigger>
            </TabsList>
            <div className="hidden items-center gap-2 rounded-xl border border-white/[0.075] bg-white/[0.026] px-3 py-2 text-xs text-slate-500 md:flex">
              <Bot className="h-4 w-4 text-cyan-100/60" aria-hidden="true" />
              Deterministic schema validation active
            </div>
          </div>

          <TabsContent value="pr">
            <WorkspaceShell
              label="INPUT SOURCE"
              source="sample_pr.diff"
              icon={<FileCode2 className="h-4 w-4 text-cyan-100/65" aria-hidden="true" />}
              action={
                <Button onClick={runPrReview} disabled={loading !== null}>
                  {loading === "pr" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Run Review
                </Button>
              }
              input={<Textarea value={prInput} onChange={(event) => setPrInput(event.target.value)} spellCheck={false} />}
              output={
                <IntelligencePanel title="PR Intelligence" subtitle="Risk analysis, conventions, and release decision">
                  {loading === "pr" ? (
                    <InvestigationState mode="pr" stageIndex={stageIndex} />
                  ) : prResult ? (
                    <div className="space-y-4">
                      <PRReview result={prResult} />
                      <RuntimeTrace result={prResult} routedModel={routedPrReviewModel?.model} />
                    </div>
                  ) : (
                    <EmptyState label="Awaiting engineering input..." />
                  )}
                </IntelligencePanel>
              }
            />
          </TabsContent>

          <TabsContent value="github">
            <WorkspaceShell
              label="GITHUB PULL REQUEST"
              source={githubOwner && githubRepo && githubPullNumber ? `${githubOwner}/${githubRepo}#${githubPullNumber}` : "Repository and PR number"}
              icon={<GitPullRequest className="h-4 w-4 text-cyan-100/65" aria-hidden="true" />}
              action={
                <Button onClick={runGithubPrReview} disabled={loading !== null || !routedPrReviewModel}>
                  {loading === "github" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Run GitHub PR Review
                </Button>
              }
              input={
                <GitHubPRForm
                  owner={githubOwner}
                  repo={githubRepo}
                  pullNumber={githubPullNumber}
                  routedModel={routedPrReviewModel}
                  repositoryContext={githubRepositoryContext}
                  postComment={githubPostComment}
                  onOwnerChange={setGithubOwner}
                  onRepoChange={setGithubRepo}
                  onPullNumberChange={setGithubPullNumber}
                  onRepositoryContextChange={setGithubRepositoryContext}
                  onPostCommentChange={setGithubPostComment}
                />
              }
              output={
                <IntelligencePanel title="GitHub PR Review" subtitle="Fetched diff, validated review, and generated PR comment">
                  {loading === "github" ? (
                    <InvestigationState mode="github" stageIndex={stageIndex} />
                  ) : githubReview ? (
                    <GitHubPRReviewResult response={githubReview} />
                  ) : (
                    <EmptyState label="No GitHub review generated." />
                  )}
                </IntelligencePanel>
              }
            />
          </TabsContent>

          <TabsContent value="incident">
            <WorkspaceShell
              label="ALERT TRIGGER"
              source={scenarioLabel(incidentScenario)}
              icon={<TerminalSquare className="h-4 w-4 text-cyan-100/65" aria-hidden="true" />}
              action={
                <Button onClick={runIncidentAutopsy} disabled={loading !== null}>
                  {loading === "incident" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                  Run Autopsy
                </Button>
              }
              input={
                <div className="space-y-5">
                  <IncidentInbox
                    incidents={incidentHistory}
                    selectedIncidentId={selectedIncidentId}
                    loaded={incidentHistoryLoaded}
                    onSelect={selectIncident}
                    onRefresh={() => refreshIncidentHistory(true).catch((err) => setError(err instanceof Error ? err.message : "Incident refresh failed"))}
                  />
                  <IncidentAlertForm
                    scenario={incidentScenario}
                    evidenceSource={incidentEvidenceSource}
                    service={incidentService}
                    severity={incidentSeverity}
                    environment={incidentEnvironment}
                    startedAt={incidentStartedAt}
                    windowMinutes={incidentWindowMinutes}
                    onEvidenceSourceChange={setIncidentEvidenceSource}
                    onScenarioChange={(value) => {
                      setIncidentScenario(value);
                      const scenario = INCIDENT_SCENARIOS.find((item) => item.id === value);
                      if (scenario) {
                        setIncidentService(scenario.service);
                        setIncidentSeverity(scenario.severity);
                        setIncidentStartedAt(scenario.startedAt);
                      }
                    }}
                    onServiceChange={setIncidentService}
                    onSeverityChange={setIncidentSeverity}
                    onEnvironmentChange={setIncidentEnvironment}
                    onStartedAtChange={setIncidentStartedAt}
                    onWindowMinutesChange={setIncidentWindowMinutes}
                  />
                </div>
              }
              output={
                <IntelligencePanel title="Incident Autopsy" subtitle="Timeline reconstruction, root cause, and prevention plan">
                  {loading === "incident" ? <InvestigationState mode="incident" stageIndex={stageIndex} /> : incidentResult ? <IncidentAutopsy result={incidentResult} /> : <EmptyState label="No incident timeline generated." />}
                </IntelligencePanel>
              }
            />
          </TabsContent>
        </Tabs>
          </>
        )}
      </div>
    </main>
  );
}

function SystemPill({ label, tone = "default" }: { label: string; tone?: "default" | "green" | "cyan" }) {
  return (
    <div className="flex h-8 items-center gap-2 rounded-lg border border-white/[0.075] bg-white/[0.026] px-3 font-semibold text-slate-400/95">
      <span
        className={
          tone === "green"
            ? "h-2 w-2 rounded-full bg-emerald-200/80 [animation:pulse-dot_1.8s_ease-in-out_infinite]"
            : tone === "cyan"
              ? "h-2 w-2 rounded-full bg-cyan-100/70"
              : "h-2 w-2 rounded-full bg-slate-500/80"
        }
      />
      {label}
    </div>
  );
}

function GitHubPRForm({
  owner,
  repo,
  pullNumber,
  routedModel,
  repositoryContext,
  postComment,
  onOwnerChange,
  onRepoChange,
  onPullNumberChange,
  onRepositoryContextChange,
  onPostCommentChange
}: {
  owner: string;
  repo: string;
  pullNumber: string;
  routedModel: RoutedModel | null;
  repositoryContext: string;
  postComment: boolean;
  onOwnerChange: (value: string) => void;
  onRepoChange: (value: string) => void;
  onPullNumberChange: (value: string) => void;
  onRepositoryContextChange: (value: string) => void;
  onPostCommentChange: (value: boolean) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <GatewayField label="Owner">
          <GatewayInput value={owner} onChange={(event) => onOwnerChange(event.target.value)} placeholder="my-org" />
        </GatewayField>
        <GatewayField label="Repository">
          <GatewayInput value={repo} onChange={(event) => onRepoChange(event.target.value)} placeholder="my-repo" />
        </GatewayField>
      </div>
      <div className="grid gap-4 md:grid-cols-[12rem_1fr]">
        <GatewayField label="Pull Request Number">
          <GatewayInput
            value={pullNumber}
            onChange={(event) => onPullNumberChange(event.target.value)}
            placeholder="12"
            inputMode="numeric"
          />
        </GatewayField>
        <ReadOnlyRoutingModel routedModel={routedModel} />
      </div>
      <GatewayField label="Repository Context">
        <Textarea
          value={repositoryContext}
          onChange={(event) => onRepositoryContextChange(event.target.value)}
          placeholder="FastAPI backend service, auth-sensitive codebase, SQLAlchemy data layer..."
          className="min-h-[11rem]"
        />
      </GatewayField>
      <label className="flex items-center gap-3 rounded-xl border border-white/[0.065] bg-white/[0.018] px-3 py-3 text-sm text-slate-300">
        <input
          type="checkbox"
          checked={postComment}
          onChange={(event) => onPostCommentChange(event.target.checked)}
          className="h-4 w-4 rounded border-white/[0.12] bg-white/[0.04]"
        />
        Post comment to GitHub
      </label>
    </div>
  );
}

function ReadOnlyRoutingModel({ routedModel }: { routedModel: RoutedModel | null }) {
  return (
    <div className="rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Review Model</p>
      {routedModel ? (
        <>
          <p className="mt-2 font-mono text-sm text-slate-200">
            {routedModel.source} → {routedModel.model}
          </p>
          <p className="mt-1 text-xs text-slate-500">Model controlled by Task Routing Settings.</p>
        </>
      ) : (
        <>
          <p className="mt-2 text-sm font-medium text-red-200/90">No PR review model configured.</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">Please configure PR_AUTOPILOT in Task Routing Settings.</p>
        </>
      )}
    </div>
  );
}

function GitHubPRReviewResult({ response }: { response: GitHubPRReviewResponse }) {
  return (
    <div className="space-y-4 animate-fade-in-up">
      <PRReview result={response.review} />
      <RuntimeTrace result={response.review} routedModel={response.model} />
      <PanelBlock title="GitHub Publication">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <Badge className={response.posted_to_github ? "border-emerald-100/14 bg-emerald-100/[0.048] text-emerald-100/90" : "border-slate-200/10 bg-slate-200/[0.04] text-slate-300/90"}>
            {response.posted_to_github ? "Posted" : "Preview Only"}
          </Badge>
          {response.github_comment_url && (
            <a
              href={response.github_comment_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 text-xs font-medium text-cyan-100/85 hover:text-cyan-100"
            >
              Open GitHub Comment
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          )}
        </div>
        <p className="text-sm leading-6 text-slate-300">
          {response.posted_to_github
            ? "The validated review was published to the pull request."
            : "Posting is disabled, so the validated review was generated as a preview only."}
        </p>
        {SHOW_DEBUG_MARKDOWN && (
          <details className="mt-4 rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
            <summary className="cursor-pointer text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Debug Markdown Payload
            </summary>
            <pre className="mt-3 max-h-[18rem] overflow-auto whitespace-pre-wrap rounded-lg bg-[#101722] p-4 font-mono text-xs leading-5 text-slate-300">
              {response.comment_body}
            </pre>
          </details>
        )}
      </PanelBlock>
    </div>
  );
}

function RuntimeTrace({ result, routedModel }: { result: PRResult; routedModel?: string }) {
  const runtime = result.runtime;
  const sourceLabel = runtime?.runtime_mode === "deterministic_demo" ? "Deterministic Demo" : runtime?.runtime_mode === "llm" ? "LLM Generated" : "Runtime Unknown";
  const grounding = runtime?.grounding_stats ?? {
    grounded: result.issues.filter((issue) => issue.grounding === "grounded").length,
    inferred: result.issues.filter((issue) => issue.grounding === "inferred").length,
    heuristic: result.issues.filter((issue) => issue.grounding === "heuristic").length,
    needs_verification: result.issues.filter((issue) => issue.grounding === "needs_verification").length
  };
  return (
    <PanelBlock title="Runtime Trace">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <TraceCell label="Source" value={sourceLabel} />
        <TraceCell label="Provider" value={runtime?.provider ?? "unknown"} />
        <TraceCell label="Model" value={runtime?.model ?? routedModel ?? "unknown"} preserveCase />
        <TraceCell label="Latency" value={formatLatency(runtime?.latency_ms, runtime?.latency_seconds)} preserveCase />
        <TraceCell label="Schema" value={runtime?.schema_name ?? "PRReviewResult"} preserveCase />
        <TraceCell label="Validation" value={runtime?.schema_validation_status ?? "passed"} />
      </div>
      <div className="mt-3 rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Grounding</p>
        <div className="mt-2 grid gap-2 text-sm text-slate-300 sm:grid-cols-2 xl:grid-cols-4">
          <span>Grounded: {grounding.grounded}</span>
          <span>Inferred: {grounding.inferred}</span>
          <span>Heuristic: {grounding.heuristic}</span>
          <span>Needs Verification: {grounding.needs_verification}</span>
        </div>
      </div>
      <div className="mt-3 rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Gateway</p>
        <p className="mt-1 font-mono text-sm text-slate-300">{runtime?.gateway ?? "Not reported by backend"}</p>
      </div>
    </PanelBlock>
  );
}

function formatLatency(latencyMs?: number | null, latencySeconds?: number | null) {
  if (typeof latencySeconds === "number" && latencySeconds >= 10) {
    return `${latencySeconds.toFixed(1)}s`;
  }
  if (typeof latencyMs === "number") {
    return latencyMs >= 1000 ? `${(latencyMs / 1000).toFixed(1)}s` : `${latencyMs} ms`;
  }
  return "not reported";
}

function formatIssueLine(issue: PRIssue) {
  if (!issue.line) return "";
  if (issue.end_line && issue.end_line !== issue.line) {
    return `:${issue.line}-${issue.end_line}`;
  }
  return `:${issue.line}`;
}

function TraceCell({ label, value, preserveCase = false }: { label: string; value: string; preserveCase?: boolean }) {
  return (
    <div className="rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-1 truncate text-sm font-medium text-slate-200">{preserveCase ? value : titleCase(value)}</p>
    </div>
  );
}

function ModelGatewaySettings({
  onLoadSamplePr,
  onRuntimeConfigSaved
}: {
  onLoadSamplePr: () => void;
  onRuntimeConfigSaved: (config: BackendRuntimeConfig) => void;
}) {
  const providers: Provider[] = ["OpenAI", "Ollama", "OpenRouter", "Custom Endpoint"];
  const [provider, setProvider] = useState<Provider>("OpenAI");
  const [model, setModel] = useState("Active Runtime");
  const [baseUrl, setBaseUrl] = useState(providerBaseUrls.OpenAI);
  const [apiKey, setApiKey] = useState("");
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<string | null>(null);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [ollamaModelsError, setOllamaModelsError] = useState<string | null>(null);
  const [loadingOllamaModels, setLoadingOllamaModels] = useState(false);
  const [registryOpen, setRegistryOpen] = useState(false);
  const [routingCandidates, setRoutingCandidates] = useState<RoutingCandidateModel[]>([]);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [evidenceTestStatus, setEvidenceTestStatus] = useState<EvidenceConnectionTestResult | null>(null);
  const [testingEvidence, setTestingEvidence] = useState(false);
  const [incidentEvidence, setIncidentEvidence] = useState<IncidentEvidenceSettings>(DEFAULT_INCIDENT_EVIDENCE_SETTINGS);
  const [incidentLogLimitInput, setIncidentLogLimitInput] = useState(String(DEFAULT_INCIDENT_EVIDENCE_SETTINGS.log_limit ?? 200));
  const [taskRouting, setTaskRouting] = useState<Record<string, string>>({
    prReview: ACTIVE_RUNTIME_OPTION,
    incidentAnalysis: ACTIVE_RUNTIME_OPTION,
    rootCauseAnalysis: ACTIVE_RUNTIME_OPTION
  });

  function updateProvider(nextProvider: Provider) {
    setProvider(nextProvider);
    setBaseUrl(providerBaseUrls[nextProvider]);
    setModel(nextProvider === "Ollama" ? "Active Runtime" : providerModels[nextProvider][0] ?? "");
    if (nextProvider === "Ollama") {
      setApiKey("");
    }
    setConnected(false);
    setConnectionStatus(null);
  }

  async function loadOllamaModels() {
    setLoadingOllamaModels(true);
    setOllamaModelsError(null);
    const modelsUrl = `${RUNTIME_API_BASE}/models`;
    try {
      const response = await fetch(modelsUrl);
      if (!response.ok) {
        throw new Error(`Unable to load Ollama models from ${modelsUrl}`);
      }
      const data = (await response.json()) as RuntimeModelsResponse;
      if (data.provider !== "ollama") {
        throw new Error(`Backend provider is ${data.provider}, not ollama`);
      }
      setOllamaModels(data.models);
      setModel((current) => (provider === "Ollama" && (!current || !data.models.includes(current)) ? data.models[0] ?? "" : current));
    } catch (err) {
      setOllamaModels([]);
      setOllamaModelsError(err instanceof Error ? err.message : `Unable to load Ollama models from ${modelsUrl}`);
      if (provider === "Ollama") {
        setModel("");
      }
    } finally {
      setLoadingOllamaModels(false);
    }
  }

  useEffect(() => {
    void loadOllamaModels();
  }, []);

  useEffect(() => {
    void loadBackendRuntimeConfig();
    const savedConfig = window.localStorage.getItem(GATEWAY_CONFIG_STORAGE_KEY);
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig) as SavedGatewayConfig;
        if (providers.includes(parsed.provider)) {
          setProvider(parsed.provider);
          setModel(parsed.model || "Active Runtime");
          setBaseUrl(parsed.baseUrl || providerBaseUrls[parsed.provider]);
          setApiKey(parsed.apiKey ?? "");
          setTemperature(parsed.temperature ?? 0.2);
          setMaxTokens(parsed.maxTokens ?? 4096);
          setRoutingCandidates((parsed.routingCandidates ?? []).slice(0, 5));
          setIncidentEvidence({
            ...DEFAULT_INCIDENT_EVIDENCE_SETTINGS,
            ...(parsed.incidentEvidence ?? {})
          });
          setIncidentLogLimitInput(String(parsed.incidentEvidence?.log_limit ?? DEFAULT_INCIDENT_EVIDENCE_SETTINGS.log_limit ?? 200));
          setTaskRouting({
            prReview: parsed.taskRouting?.prReview ?? ACTIVE_RUNTIME_OPTION,
            incidentAnalysis: parsed.taskRouting?.incidentAnalysis ?? ACTIVE_RUNTIME_OPTION,
            rootCauseAnalysis: parsed.taskRouting?.rootCauseAnalysis ?? ACTIVE_RUNTIME_OPTION
          });
          return;
        }
      } catch {
        window.localStorage.removeItem(GATEWAY_CONFIG_STORAGE_KEY);
      }
    }

    const stored = window.localStorage.getItem(ROUTING_MODELS_STORAGE_KEY);
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored) as RoutingCandidateModel[];
      if (Array.isArray(parsed)) {
        setRoutingCandidates(parsed.slice(0, 5));
      }
    } catch {
      window.localStorage.removeItem(ROUTING_MODELS_STORAGE_KEY);
    }
  }, []);

  async function loadBackendRuntimeConfig() {
    try {
      const backendConfig = await getJson<BackendRuntimeConfig>("/runtime-config");
      window.localStorage.setItem("devsentinel-backend-runtime-config", JSON.stringify(backendConfig));
      const partial = backendConfigToSavedConfig(backendConfig);
      if (partial.taskRouting) {
        setTaskRouting((current) => ({
          ...current,
          prReview: partial.taskRouting?.prReview ?? current.prReview,
          incidentAnalysis: partial.taskRouting?.incidentAnalysis ?? current.incidentAnalysis,
          rootCauseAnalysis: partial.taskRouting?.rootCauseAnalysis ?? current.rootCauseAnalysis,
        }));
      }
      if (partial.provider) {
        setProvider(partial.provider);
      }
      if (partial.model) {
        setModel(partial.model);
      }
      if (partial.baseUrl) {
        setBaseUrl(partial.baseUrl);
      }
      if (typeof partial.apiKey === "string") {
        setApiKey(partial.apiKey);
      }
      if (partial.incidentEvidence) {
        setIncidentEvidence((current) => ({
          ...current,
          ...partial.incidentEvidence
        }));
        setIncidentLogLimitInput(String(partial.incidentEvidence.log_limit ?? DEFAULT_INCIDENT_EVIDENCE_SETTINGS.log_limit ?? 200));
      }
    } catch {
      // Keep local settings usable when the backend is not running.
    }
  }

  useEffect(() => {
    window.localStorage.setItem(ROUTING_MODELS_STORAGE_KEY, JSON.stringify(routingCandidates));
  }, [routingCandidates]);

  function currentRuntimeProviderConfig(): BackendRuntimeProviderConfig {
    return {
      provider: backendProviderFromUi(provider),
      base_url: provider === "Ollama" ? providerBaseUrls.Ollama : baseUrl,
      model: modelFromSelection(model) ?? model,
      api_key: provider === "Ollama" ? null : apiKey
    };
  }

  async function testConnection() {
    setConnected(false);
    setConnectionStatus("Testing runtime connection...");
    try {
      const result = await postJson<RuntimeConnectionTestResult>("/runtime-config/test", {
        model_gateway: currentRuntimeProviderConfig()
      });
      setConnected(result.ok);
      setConnectionStatus(result.ok ? `Connection verified (${result.models.length} models available)` : result.detail);
    } catch (err) {
      setConnectionStatus(err instanceof Error ? err.message : "Connection test failed");
    }
  }

  async function testEvidenceConnection() {
    setTestingEvidence(true);
    setEvidenceTestStatus(null);
    try {
      const result = await postJson<EvidenceConnectionTestResult>("/incidents/evidence/test", incidentEvidence);
      setEvidenceTestStatus(result);
    } catch (err) {
      setEvidenceTestStatus({
        provider: incidentEvidence.provider ?? "unknown",
        ok: false,
        checks: [
          {
            name: "request",
            ok: false,
            detail: err instanceof Error ? err.message : "Evidence connection test failed"
          }
        ]
      });
    } finally {
      setTestingEvidence(false);
    }
  }

  async function saveGatewayConfiguration() {
    const config: SavedGatewayConfig = {
      provider,
      model,
      baseUrl,
      apiKey,
      temperature,
      maxTokens,
      routingCandidates,
      taskRouting,
      incidentEvidence
    };
    window.localStorage.setItem(GATEWAY_CONFIG_STORAGE_KEY, JSON.stringify(config));
    window.localStorage.setItem(ROUTING_MODELS_STORAGE_KEY, JSON.stringify(routingCandidates));
    try {
      const backendConfig = await putJson<BackendRuntimeConfig>("/runtime-config", savedConfigToBackendConfig(config));
      window.localStorage.setItem("devsentinel-backend-runtime-config", JSON.stringify(backendConfig));
      onRuntimeConfigSaved(backendConfig);
      setSaveStatus("Gateway configuration saved to backend runtime");
    } catch (err) {
      setSaveStatus(err instanceof Error ? `Saved locally only: ${err.message}` : "Saved locally only");
    } finally {
      window.setTimeout(() => setSaveStatus(null), 3200);
    }
  }

  function toRoutingCandidate(providerName: string, modelName: string): RoutingCandidateModel {
    return {
      id: `${providerName}:${modelName}`,
      provider: providerName,
      model: modelName,
      label: `${providerName} / ${modelName}`
    };
  }

  function toggleRoutingCandidate(providerName: string, modelName: string) {
    const candidate = toRoutingCandidate(providerName, modelName);
    setRoutingCandidates((current) => {
      if (current.some((item) => item.id === candidate.id)) {
        return current.filter((item) => item.id !== candidate.id);
      }
      if (current.length >= 5) {
        return current;
      }
      return [...current, candidate];
    });
  }

  const routingOptions = [ACTIVE_RUNTIME_OPTION, ...routingCandidates.map((candidate) => candidate.label)];
  const runtimeModelOptions = provider === "Ollama" ? ["Active Runtime", ...ollamaModels] : ["Active Runtime", ...routingCandidates.map((candidate) => candidate.label)];
  const evidenceProviderOptions: IncidentEvidenceProvider[] = ["fixture", "local_file", "datadog", "loki_prometheus"];
  const discoveredModelGroups = [
    { provider: "Ollama", models: ollamaModels },
    { provider: "OpenAI", models: providerModels.OpenAI },
    { provider: "OpenRouter", models: providerModels.OpenRouter }
  ];

  return (
    <section className="animate-fade-in-up">
      <div className="max-w-6xl">
      <div className="flex flex-col gap-5 border-b border-white/[0.045] pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Settings / Model Gateway</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-100">Model Gateway</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            AI Runtime Orchestration for DevSentinel.
          </p>
        </div>
        <div className="min-w-[18rem] border-l border-white/[0.045] pl-5">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-200/80" />
            Active Runtime
          </div>
          <p className="mt-2 font-mono text-sm text-slate-200">{provider} / {model}</p>
          <p className="mt-1 text-xs text-slate-500">{provider === "Ollama" ? "Local Runtime" : "Cloud Runtime"} · {connected ? "Connected" : "Ready"}</p>
        </div>
      </div>

      <div>
        <div className="py-2">
          <GatewayStep
            step="01"
            title="Select Provider"
            description="Choose the model gateway DevSentinel should use for inference requests."
          >
            <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_12rem]">
              <GatewayField label="Provider">
                <GatewaySelect value={provider} onChange={(value) => updateProvider(value as Provider)} options={providers} />
              </GatewayField>
              <RuntimeBadge label={provider === "Ollama" ? "Local runtime" : "Cloud runtime"} />
            </div>
          </GatewayStep>

          <GatewayStep
            step="02"
            title="Runtime Configuration"
            description="Define connection details and model behavior, then verify the runtime path."
          >
            <div className="grid gap-4 md:grid-cols-2">
              {provider === "Ollama" ? (
                <>
                  <GatewayField label="Base URL">
                    <GatewayInput icon={Server} value="http://localhost:11434" readOnly />
                  </GatewayField>
                  <GatewayField label="Runtime Model">
                    <GatewaySelect value={model} onChange={setModel} options={runtimeModelOptions} />
                  </GatewayField>
                </>
              ) : (
                <>
                  <GatewayField label="Base URL">
                    <GatewayInput icon={Server} value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder={providerBaseUrls[provider] || "https://your-provider.example/v1"} />
                  </GatewayField>
                  <GatewayField label="API Key">
                    <GatewayInput icon={KeyRound} type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder={provider === "OpenAI" ? "sk-..." : "paste provider key"} autoComplete="off" />
                  </GatewayField>
                  <GatewayField label="Runtime Model">
                    <GatewayInput value={model} onChange={(event) => setModel(event.target.value)} placeholder={providerModels[provider][0] ?? "provider/model-name"} />
                  </GatewayField>
                  <GatewayField label={`Temperature: ${temperature.toFixed(1)}`}>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={temperature}
                      onChange={(event) => setTemperature(Number(event.target.value))}
                      className="h-2 w-full accent-emerald-200"
                    />
                  </GatewayField>
                  <GatewayField label="Max Tokens">
                    <GatewayInput type="number" value={String(maxTokens)} onChange={(event) => setMaxTokens(Number(event.target.value))} />
                  </GatewayField>
                </>
              )}
            </div>
            <div className="mt-5 flex flex-wrap items-center gap-3">
              {provider === "Ollama" && (
                <Button variant="secondary" onClick={loadOllamaModels} disabled={loadingOllamaModels}>
                  {loadingOllamaModels ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plug className="h-4 w-4" />}
                  Refresh Ollama Models
                </Button>
              )}
              <Button onClick={testConnection}>
                <Plug className="h-4 w-4" />
                Test Connection
              </Button>
              {connectionStatus && (
                <div className={`flex items-center gap-2 text-sm ${connected ? "text-emerald-100/85" : "text-red-200/90"}`}>
                  {connected ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                  {connectionStatus}
                </div>
              )}
            </div>
            {provider === "Ollama" && ollamaModelsError && <p className="mt-3 text-sm text-red-200/90">{ollamaModelsError}</p>}
            {provider === "Ollama" && !ollamaModelsError && (
              <p className="mt-3 text-xs text-slate-500">
                Models are loaded from backend /models, sourced from Ollama /api/tags.
              </p>
            )}
          </GatewayStep>

          <GatewayStep
            step="03"
            title="Routing Model Registry"
            description="Discover available models and choose up to five routing candidates."
          >
            <details
              open={registryOpen}
              onToggle={(event) => setRegistryOpen(event.currentTarget.open)}
              className="rounded-xl bg-white/[0.014] p-3"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-medium text-slate-200">
                <span>{routingCandidates.length}/5 routing candidate models selected</span>
                <ChevronDown className={`h-4 w-4 text-slate-600 transition-transform ${registryOpen ? "rotate-180" : ""}`} />
              </summary>
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                {discoveredModelGroups.map((group) => (
                  <div key={group.provider} className="min-w-0 rounded-xl bg-white/[0.014] p-3">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{group.provider}</p>
                      {group.provider === "Ollama" && (
                        <Button size="sm" variant="ghost" onClick={loadOllamaModels} disabled={loadingOllamaModels}>
                          {loadingOllamaModels ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plug className="h-4 w-4" />}
                          Refresh
                        </Button>
                      )}
                    </div>
                    {group.provider === "Ollama" && ollamaModelsError ? (
                      <p className="text-xs leading-5 text-red-200/90">{ollamaModelsError}</p>
                    ) : group.models.length > 0 ? (
                      <div className="max-h-64 space-y-2 overflow-auto pr-1">
                        {group.models.map((modelName) => {
                          const candidate = toRoutingCandidate(group.provider, modelName);
                          const checked = routingCandidates.some((item) => item.id === candidate.id);
                          const disabled = !checked && routingCandidates.length >= 5;
                          return (
                            <label
                              key={candidate.id}
                              className={`flex min-w-0 items-center gap-3 rounded-lg px-2 py-2 text-sm ${disabled ? "text-slate-600" : "text-slate-300 hover:bg-white/[0.025]"}`}
                            >
                              <input
                                type="checkbox"
                                checked={checked}
                                disabled={disabled}
                                onChange={() => toggleRoutingCandidate(group.provider, modelName)}
                                className="h-4 w-4 accent-emerald-200"
                              />
                              <span className="truncate font-mono text-xs">{modelName}</span>
                            </label>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-xs leading-5 text-slate-500">No models discovered.</p>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-xl bg-white/[0.014] p-3">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Routing Candidate Models</p>
                {routingCandidates.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {routingCandidates.map((candidate) => (
                      <Badge key={candidate.id} className="border-cyan-100/14 bg-cyan-100/[0.045] text-cyan-100/90">
                        {candidate.label}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">Select models above to make them available for routing.</p>
                )}
              </div>
            </details>
          </GatewayStep>

          <GatewayStep
            step="04"
            title="Task Routing"
            description="Route each AI workflow to the runtime best suited for its reasoning profile."
          >
            <div className="space-y-3">
              <GatewayRoute
                label="PR Review"
                options={routingOptions}
                value={taskRouting.prReview}
                onChange={(value) => setTaskRouting((current) => ({ ...current, prReview: value }))}
                defaultValue={ACTIVE_RUNTIME_OPTION}
              />
              <GatewayRoute
                label="Incident Analysis"
                options={routingOptions}
                value={taskRouting.incidentAnalysis}
                onChange={(value) => setTaskRouting((current) => ({ ...current, incidentAnalysis: value }))}
                defaultValue={ACTIVE_RUNTIME_OPTION}
              />
              <GatewayRoute
                label="Root Cause Analysis"
                options={routingOptions}
                value={taskRouting.rootCauseAnalysis}
                onChange={(value) => setTaskRouting((current) => ({ ...current, rootCauseAnalysis: value }))}
                defaultValue={ACTIVE_RUNTIME_OPTION}
              />
            </div>
          </GatewayStep>

          <GatewayStep
            step="05"
            title="Incident Evidence"
            description="Choose the default evidence source for Incident Autopsy webhook runs."
          >
            <div className="grid gap-4 md:grid-cols-2">
              <GatewayField label="Evidence Provider">
                <GatewaySelect
                  value={incidentEvidence.provider ?? "fixture"}
                  onChange={(value) => setIncidentEvidence((current) => ({ ...current, provider: value as IncidentEvidenceProvider }))}
                  options={evidenceProviderOptions}
                />
              </GatewayField>
              <GatewayField label="Log Limit">
                <GatewayInput
                  type="number"
                  min={1}
                  max={1000}
                  value={incidentLogLimitInput}
                  onChange={(event) => {
                    const nextValue = event.target.value;
                    setIncidentLogLimitInput(nextValue);
                    if (nextValue === "") {
                      setIncidentEvidence((current) => ({ ...current, log_limit: null }));
                      return;
                    }
                    const parsed = Number(nextValue);
                    if (Number.isFinite(parsed)) {
                      setIncidentEvidence((current) => ({
                        ...current,
                        log_limit: Math.min(Math.max(Math.trunc(parsed), 1), 1000)
                      }));
                    }
                  }}
                  onBlur={() => {
                    const nextLimit = incidentEvidence.log_limit ?? 200;
                    setIncidentLogLimitInput(String(nextLimit));
                  }}
                />
              </GatewayField>
              <GatewayField label="Local Log Path">
                <GatewayInput
                  icon={FileCode2}
                  value={incidentEvidence.log_file_path ?? ""}
                  onChange={(event) => setIncidentEvidence((current) => ({ ...current, log_file_path: event.target.value }))}
                />
              </GatewayField>
              <GatewayField label="Datadog Site">
                <GatewayInput
                  icon={Network}
                  value={incidentEvidence.datadog_site ?? ""}
                  onChange={(event) => setIncidentEvidence((current) => ({ ...current, datadog_site: event.target.value }))}
                />
              </GatewayField>
              <GatewayField label="Loki Base URL">
                <GatewayInput
                  icon={Server}
                  value={incidentEvidence.loki_base_url ?? ""}
                  onChange={(event) => setIncidentEvidence((current) => ({ ...current, loki_base_url: event.target.value }))}
                />
              </GatewayField>
              <GatewayField label="Prometheus Base URL">
                <GatewayInput
                  icon={Activity}
                  value={incidentEvidence.prometheus_base_url ?? ""}
                  onChange={(event) => setIncidentEvidence((current) => ({ ...current, prometheus_base_url: event.target.value }))}
                />
              </GatewayField>
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">
              Datadog API credentials stay in backend environment variables. The UI saves provider selection and non-secret endpoints only.
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-3">
              <Button variant="secondary" onClick={testEvidenceConnection} disabled={testingEvidence}>
                {testingEvidence ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plug className="h-4 w-4" />}
                Test Evidence Connection
              </Button>
              {evidenceTestStatus && (
                <div className={`flex items-center gap-2 text-sm ${evidenceTestStatus.ok ? "text-emerald-100/85" : "text-red-200/90"}`}>
                  {evidenceTestStatus.ok ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                  {evidenceTestStatus.provider}: {evidenceTestStatus.ok ? "reachable" : "needs attention"}
                </div>
              )}
            </div>
            {evidenceTestStatus && (
              <div className="mt-3 space-y-2">
                {evidenceTestStatus.checks.map((check) => (
                  <div key={check.name} className="rounded-xl bg-white/[0.014] p-3 text-xs leading-5 text-slate-400">
                    <span className={check.ok ? "text-emerald-100/85" : "text-red-200/90"}>{check.name}</span>
                    <span className="text-slate-600"> / </span>
                    {check.detail}
                  </div>
                ))}
              </div>
            )}
          </GatewayStep>

          <GatewayStep
            step="06"
            title="Load Sample PR"
            description="Prepare the PR Autopilot workbench with a representative security-focused diff."
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-medium text-slate-200">Sample PR diff ready</p>
                <p className="mt-1 text-xs text-slate-500">Loads the demo diff into the PR input without changing gateway settings.</p>
              </div>
              <Button onClick={onLoadSamplePr}>
                <FileCode2 className="h-4 w-4" />
                Load Sample PR
              </Button>
            </div>
          </GatewayStep>

          <GatewayStep
            step="07"
            title="Runtime Safeguards"
            description="Operational controls enforced before model output reaches DevSentinel workflows."
          >
            <div className="grid gap-3 text-sm text-slate-300 md:grid-cols-2">
              <RuntimeSafeguard label="Schema validation enforced" />
              <RuntimeSafeguard label="Deterministic temperature policy" />
              <RuntimeSafeguard label="Automatic fallback runtime" />
              <RuntimeSafeguard label="Runtime isolation enabled" />
            </div>
          </GatewayStep>

          <GatewayStep
            step="08"
            title="Save Configuration"
            description="Persist this orchestration profile for DevSentinel runtime execution."
          >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Ready to apply gateway configuration</p>
              <p className="mt-1 text-xs text-slate-500">Settings remain local until saved.</p>
            </div>
            <Button onClick={saveGatewayConfiguration}>
              <Save className="h-4 w-4" />
              Save Gateway Configuration
            </Button>
          </div>
          {saveStatus && (
            <div className="mt-3 flex items-center gap-2 text-sm text-emerald-100/85">
              <CheckCircle2 className="h-4 w-4" />
              {saveStatus}
            </div>
          )}
          </GatewayStep>
        </div>

        <section className="mt-8 border-t border-white/[0.045] pt-7">
          <div className="mb-3 flex items-end justify-between gap-4">
            <div>
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">Saved Gateways</p>
              <p className="mt-1 text-sm text-slate-500">Reusable runtime targets available for routing.</p>
            </div>
          </div>
          <div className="space-y-2">
            {[
              ["OpenAI", "gpt-4.1", "Cloud Runtime", "Connected"],
              ["Ollama", "qwen2.5-coder", "Local Runtime", "Active"],
              ["OpenRouter", "DeepSeek-R1", "Cloud Runtime", "Standby"]
            ].map(([name, savedModel, locality, state]) => (
              <SavedGateway key={`${name}-${savedModel}`} name={name} model={savedModel} runtime={locality} state={state} />
            ))}
          </div>
        </section>
      </div>
      </div>
    </section>
  );
}

function GatewayField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</span>
      {children}
    </label>
  );
}

function GatewayStep({
  step,
  title,
  description,
  children
}: {
  step: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="grid gap-8 border-b border-white/[0.035] py-9 last:border-0 md:grid-cols-[13rem_1fr]">
      <div>
        <p className="font-mono text-xs text-slate-600">{step}</p>
        <h3 className="mt-2 text-base font-semibold text-slate-100">{title}</h3>
        <p className="mt-2 text-xs leading-5 text-slate-500">{description}</p>
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  );
}

function RuntimeBadge({ label }: { label: string }) {
  return (
    <div className="flex h-11 items-center gap-2 rounded-xl bg-white/[0.018] px-3 text-sm text-slate-300">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-400/70" />
      {label}
    </div>
  );
}

function GatewayInput({ icon: Icon, className = "", ...props }: React.InputHTMLAttributes<HTMLInputElement> & { icon?: React.ElementType }) {
  return (
    <div className="relative">
      {Icon && <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" aria-hidden="true" />}
      <input
        className={`h-11 w-full rounded-xl border border-white/[0.045] bg-white/[0.022] px-3 text-sm text-slate-200 outline-none transition-colors placeholder:text-slate-600 focus:border-white/10 focus:bg-white/[0.04] ${Icon ? "pl-9" : ""} ${className}`}
        {...props}
      />
    </div>
  );
}

function GatewaySelect({ value, onChange, options, disabled = false }: { value: string; onChange: (value: string) => void; options: string[]; disabled?: boolean }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        className="h-11 w-full appearance-none rounded-xl border border-white/[0.045] bg-white/[0.022] px-3 pr-9 text-sm text-slate-200 outline-none transition-colors focus:border-white/10 focus:bg-white/[0.04]"
      >
        {options.map((option) => (
          <option key={option} value={option} className="bg-[#101720]">
            {option}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" aria-hidden="true" />
    </div>
  );
}

function GatewayStatus({ connected }: { connected: boolean }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-lg bg-white/[0.025] px-2.5 py-1 text-xs font-medium text-slate-300">
      <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-emerald-200/80" : "bg-slate-500/80"}`} />
      {connected ? "Connected" : "Ready"}
    </span>
  );
}

function GatewayRoute({
  label,
  options,
  value,
  onChange,
  defaultValue
}: {
  label: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
  defaultValue: string;
}) {
  useEffect(() => {
    if (!options.includes(value)) {
      onChange(defaultValue);
    }
  }, [defaultValue, onChange, options, value]);

  return (
    <div className="grid gap-3 rounded-xl bg-white/[0.014] p-3 md:grid-cols-[13rem_1rem_1fr] md:items-center">
      <div>
        <p className="text-sm font-medium text-slate-200">{label}</p>
        <p className="mt-1 text-xs text-slate-500">AI workflow route</p>
      </div>
      <span className="hidden text-slate-600 md:block">→</span>
      <GatewaySelect value={value} onChange={onChange} options={options} />
    </div>
  );
}

function RuntimeSafeguard({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-white/[0.014] p-3">
      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-100/75" />
      <span>{label}</span>
    </div>
  );
}

function SavedGateway({ name, model, runtime, state }: { name: string; model: string; runtime: string; state: string }) {
  return (
    <div className="flex flex-col gap-2 rounded-xl bg-white/[0.014] px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${state === "Active" ? "bg-emerald-200/80" : state === "Connected" ? "bg-slate-300/70" : "bg-slate-600"}`} />
        <div className="min-w-0">
          <p className="font-medium text-slate-200">{name}</p>
          <p className="mt-1 truncate font-mono text-xs text-slate-500">
            {model} · {runtime} · {state}
          </p>
        </div>
      </div>
      <span className="text-xs text-slate-600">Reusable runtime</span>
    </div>
  );
}

function PolicyRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-white/[0.05] pb-3 last:border-0 last:pb-0">
      <span>{label}</span>
      <span className="font-medium text-slate-200">{value}</span>
    </div>
  );
}

function PolicyInline({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/[0.018] p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-200">{value}</p>
    </div>
  );
}

function WorkspaceShell({
  label,
  source,
  icon,
  action,
  input,
  output
}: {
  label: string;
  source: string;
  icon: React.ReactNode;
  action: React.ReactNode;
  input: React.ReactNode;
  output: React.ReactNode;
}) {
  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(30rem,0.92fr)]">
      <div className="rounded-2xl border border-white/[0.075] bg-[hsl(var(--surface))] shadow-[0_10px_26px_rgba(0,0,0,0.12)]">
        <div className="flex items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.07] bg-white/[0.026]">{icon}</div>
            <div>
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
              <p className="font-mono text-xs text-slate-300/90">{source}</p>
            </div>
          </div>
          {action}
        </div>
        <div className="p-4">{input}</div>
      </div>
      {output}
    </section>
  );
}

function IntelligencePanel({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <aside className="rounded-2xl border border-white/[0.075] bg-[hsl(var(--surface))] shadow-[0_10px_26px_rgba(0,0,0,0.12)]">
      <div className="relative overflow-hidden border-b border-white/[0.06] px-5 py-4">
        <div className="absolute inset-x-0 top-0 h-px bg-slate-200/[0.055] [animation:scanline_6s_linear_infinite]" />
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-100">{title}</h2>
            <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>
          </div>
          <Badge className="border-emerald-100/14 bg-emerald-100/[0.048] text-emerald-100/90">Validated</Badge>
        </div>
      </div>
      <div className="max-h-[calc(100vh-13rem)] overflow-auto p-5">{children}</div>
    </aside>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex min-h-[32rem] items-center justify-center rounded-xl border border-dashed border-white/[0.065] bg-white/[0.018] p-4 text-center text-sm text-slate-500">
      {label}
    </div>
  );
}

function InvestigationState({ mode, stageIndex }: { mode: LoadingMode; stageIndex: number }) {
  const stages = INVESTIGATION_STAGES[mode];
  return (
    <div className="min-h-[32rem] rounded-xl border border-white/[0.07] bg-[#101722] p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.07] bg-white/[0.026]">
          <Loader2 className="h-5 w-5 animate-spin text-cyan-100/65" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-100">AI investigation running</p>
          <p className="text-xs text-slate-500">Structured reasoning pipeline active</p>
        </div>
      </div>
      <div className="space-y-3">
        {stages.map((stage, index) => {
          const active = index === stageIndex;
          const complete = index < stageIndex;
          return (
            <div
              key={stage}
              className={`flex items-center gap-3 rounded-xl border px-3 py-3 transition-all ${
                active
                  ? "border-cyan-100/14 bg-cyan-100/[0.045] text-cyan-100/90"
                  : complete
                    ? "border-emerald-100/14 bg-emerald-100/[0.045] text-emerald-100/90"
                    : "border-white/[0.065] bg-white/[0.018] text-slate-500"
              }`}
            >
              {complete ? <CheckCircle2 className="h-4 w-4 text-emerald-100/75" /> : <span className={`h-2.5 w-2.5 rounded-full ${active ? "bg-cyan-100/75 [animation:pulse-dot_1.4s_ease-in-out_infinite]" : "bg-slate-600/80"}`} />}
              <span className="text-sm font-medium">{stage}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PRReview({ result }: { result: PRResult }) {
  const groundedCount = result.issues.filter((issue) => issue.grounding === "grounded").length;
  const needsVerificationCount = result.issues.filter((issue) => issue.grounding === "inferred" || issue.grounding === "heuristic" || issue.grounding === "needs_verification").length;

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <Metric label="Decision" value={titleCase(result.decision)} tone="amber" />
        <Metric label="Grounded" value={String(groundedCount)} tone="green" />
        <Metric label="Needs Verification" value={String(needsVerificationCount)} tone="cyan" />
        <Metric label="Findings" value={String(result.issues.length)} tone="green" />
      </div>
      <PanelBlock title="Review Summary">
        <p className="text-sm leading-6 text-slate-300">{result.summary}</p>
      </PanelBlock>
      <div className="space-y-3">
        {result.issues.map((issue, index) => (
          <article
            key={`${issue.title}-${issue.line}`}
            className="animate-fade-in-up rounded-2xl border border-white/[0.07] bg-[hsl(var(--surface-elevated))] p-5 shadow-[0_8px_22px_rgba(0,0,0,0.1)] transition-colors hover:border-white/10"
            style={{ animationDelay: `${index * 80}ms` }}
          >
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Badge className={severityClass(issue.severity)}>{issue.severity}</Badge>
              <Badge className="border-cyan-100/14 bg-cyan-100/[0.045] text-cyan-100/90">{issue.category}</Badge>
              <Badge className="border-emerald-100/14 bg-emerald-100/[0.045] text-emerald-100/90">{titleCase(issue.grounding)}</Badge>
              <span className="font-mono text-xs text-slate-500">
                {issue.file}
                {formatIssueLine(issue)}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-slate-100">{issue.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{issue.reasoning}</p>
            <div className="mt-4 rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
              <p className="mb-1 text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">Suggested Fix</p>
              <p className="text-sm leading-6 text-slate-300">{issue.suggested_fix}</p>
            </div>
            <ul className="mt-3 space-y-1 text-xs leading-5 text-slate-500">
              {issue.skill_references.map((reference) => (
                <li key={reference}>{reference}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </div>
  );
}

function IncidentInbox({
  incidents,
  selectedIncidentId,
  loaded,
  onSelect,
  onRefresh
}: {
  incidents: StoredIncident[];
  selectedIncidentId: string | null;
  loaded: boolean;
  onSelect: (incident: StoredIncident) => void;
  onRefresh: () => void;
}) {
  return (
    <section className="rounded-xl border border-white/[0.07] bg-white/[0.018] p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-slate-500">Incident Inbox</p>
          <p className="mt-1 text-xs text-slate-500">Auto-refreshes webhook analyses every 5 seconds.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={onRefresh}>
          <Activity className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>
      {!loaded ? (
        <p className="rounded-lg border border-white/[0.06] bg-[#0f1722] px-3 py-3 text-sm text-slate-500">Loading incidents...</p>
      ) : incidents.length === 0 ? (
        <p className="rounded-lg border border-dashed border-white/[0.06] bg-[#0f1722] px-3 py-3 text-sm text-slate-500">No saved incident analyses yet.</p>
      ) : (
        <div className="max-h-72 space-y-2 overflow-auto pr-1">
          {incidents.slice(0, 8).map((incident) => {
            const selected = incident.id === selectedIncidentId;
            const evidence = incident.report.runtime?.evidence_counts;
            const evidenceCount = evidence ? evidence.logs + evidence.metrics + evidence.deployments + evidence.traces : 0;
            return (
              <button
                key={incident.id}
                type="button"
                onClick={() => onSelect(incident)}
                className={`w-full rounded-xl border p-3 text-left transition-colors ${
                  selected
                    ? "border-cyan-100/18 bg-cyan-100/[0.05]"
                    : "border-white/[0.06] bg-[#0f1722] hover:border-white/10 hover:bg-white/[0.028]"
                }`}
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge className={severityClass(incident.severity)}>{incident.severity}</Badge>
                  <Badge className="border-emerald-100/14 bg-emerald-100/[0.045] text-emerald-100/90">{incident.status}</Badge>
                  <span className="font-mono text-[0.68rem] text-slate-500">{formatLocalDateTime(incident.created_at)}</span>
                </div>
                <p className="line-clamp-2 text-sm font-semibold text-slate-100">{incident.report.incident_title}</p>
                <p className="mt-1 truncate text-xs text-slate-500">
                  {incident.service} / {incident.environment} / {incident.source} / {evidenceCount} evidence
                </p>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}

function IncidentAlertForm({
  scenario,
  evidenceSource,
  service,
  severity,
  environment,
  startedAt,
  windowMinutes,
  onEvidenceSourceChange,
  onScenarioChange,
  onServiceChange,
  onSeverityChange,
  onEnvironmentChange,
  onStartedAtChange,
  onWindowMinutesChange
}: {
  scenario: string;
  evidenceSource: IncidentEvidenceProvider;
  service: string;
  severity: "sev1" | "sev2" | "sev3" | "sev4";
  environment: string;
  startedAt: string;
  windowMinutes: string;
  onEvidenceSourceChange: (value: IncidentEvidenceProvider) => void;
  onScenarioChange: (value: string) => void;
  onServiceChange: (value: string) => void;
  onSeverityChange: (value: "sev1" | "sev2" | "sev3" | "sev4") => void;
  onEnvironmentChange: (value: string) => void;
  onStartedAtChange: (value: string) => void;
  onWindowMinutesChange: (value: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="mb-2 block text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-slate-500">Evidence Source</label>
        <select
          value={evidenceSource}
          onChange={(event) => onEvidenceSourceChange(event.target.value as IncidentEvidenceProvider)}
          className="h-10 w-full rounded-xl border border-white/[0.075] bg-[#0f1722] px-3 text-sm text-slate-200 outline-none"
        >
          <option value="fixture">Fixture Evidence Packet</option>
          <option value="local_file">Local Log File</option>
          <option value="datadog">Datadog</option>
          <option value="loki_prometheus">Loki + Prometheus</option>
        </select>
      </div>
      <div>
        <label className="mb-2 block text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-slate-500">Scenario Provider</label>
        <select
          value={scenario}
          onChange={(event) => onScenarioChange(event.target.value)}
          className="h-10 w-full rounded-xl border border-white/[0.075] bg-[#0f1722] px-3 text-sm text-slate-200 outline-none"
        >
          {INCIDENT_SCENARIOS.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <LabeledInput label="Service" value={service} onChange={onServiceChange} />
        <div>
          <label className="mb-2 block text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-slate-500">Severity</label>
          <select
            value={severity}
            onChange={(event) => onSeverityChange(event.target.value as "sev1" | "sev2" | "sev3" | "sev4")}
            className="h-10 w-full rounded-xl border border-white/[0.075] bg-[#0f1722] px-3 text-sm text-slate-200 outline-none"
          >
            {["sev1", "sev2", "sev3", "sev4"].map((item) => (
              <option key={item} value={item}>
                {item.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
        <LabeledInput label="Environment" value={environment} onChange={onEnvironmentChange} />
        <LabeledInput label="Window Minutes" value={windowMinutes} onChange={onWindowMinutesChange} />
      </div>
      <LabeledInput label="Started At" value={startedAt} onChange={onStartedAtChange} />
      <div className="rounded-xl border border-cyan-100/10 bg-cyan-100/[0.035] p-3 text-xs leading-5 text-cyan-50/75">
        The selected fixture only supplies raw incident evidence. The report is generated by the active INCIDENT_AUTOPSY runtime and then schema-validated.
      </div>
    </div>
  );
}

function LabeledInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div>
      <label className="mb-2 block text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</label>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-xl border border-white/[0.075] bg-[#0f1722] px-3 text-sm text-slate-200 outline-none"
      />
    </div>
  );
}

function IncidentAutopsy({ result }: { result: IncidentResult }) {
  const runtime = result.runtime;
  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <Metric label="Source" value={runtime?.runtime_mode === "deterministic_demo" ? "Demo" : "LLM"} tone="cyan" />
        <Metric label="Schema" value={runtime?.schema_validation_status ? "Passed" : "Validated"} tone="green" />
        <Metric label="Latency" value={runtime?.latency_seconds ? `${runtime.latency_seconds.toFixed(1)}s` : "n/a"} tone="amber" />
        <Metric label="Evidence" value={runtime ? `${runtime.evidence_counts.logs + runtime.evidence_counts.metrics + runtime.evidence_counts.deployments + runtime.evidence_counts.traces} items` : "packet"} tone="red" />
      </div>
      <PanelBlock title={result.incident_title}>
        <p className="text-sm leading-6 text-slate-300">{result.executive_summary}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {result.affected_services.map((service) => (
            <Badge key={service} className="border-cyan-100/14 bg-cyan-100/[0.045] text-cyan-100/90">
              {service}
            </Badge>
          ))}
        </div>
      </PanelBlock>
      <PanelBlock title="Most Likely Root Cause">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge className={groundingClass(result.most_likely_root_cause.grounding)}>{titleCase(result.most_likely_root_cause.grounding)}</Badge>
          {result.most_likely_root_cause.supporting_evidence.map((ref) => (
            <Badge key={ref} className="border-slate-200/10 bg-slate-200/[0.04] text-slate-300/90">{ref}</Badge>
          ))}
        </div>
        <p className="text-sm font-semibold text-slate-100">{result.most_likely_root_cause.title}</p>
        <p className="mt-2 text-sm leading-6 text-slate-300">{result.most_likely_root_cause.explanation}</p>
        <p className="mt-2 text-xs leading-5 text-slate-500">{result.most_likely_root_cause.uncertainty}</p>
      </PanelBlock>
      <PanelBlock title="Incident Timeline">
        <div className="relative space-y-0 pl-6">
          <div className="absolute bottom-3 left-[0.55rem] top-3 w-px bg-white/[0.065]" />
          {result.timeline.map((item, index) => {
            const tone = timelineTone(item.summary);
            const time = item.timestamp.slice(11, 16);
            return (
              <div key={`${item.timestamp}-${item.summary}`} className="relative pb-5 last:pb-0">
                <span className={`absolute -left-[1.05rem] top-1 h-3 w-3 rounded-full border ${toneDotClass(tone)}`} />
                <div
                  className="animate-fade-in-up rounded-xl border border-white/[0.07] bg-[hsl(var(--surface-elevated))] p-4"
                  style={{ animationDelay: `${index * 70}ms` }}
                >
                  <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-xs font-semibold text-slate-400">{time}</span>
                    <Badge className={groundingClass(item.grounding)}>{item.grounding}</Badge>
                  </div>
                  <p className="text-sm font-semibold text-slate-100">{item.summary}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{item.service} / {item.event_type} / {item.evidence_refs.join(", ")}</p>
                </div>
              </div>
            );
          })}
        </div>
      </PanelBlock>
      <PanelBlock title="Root Cause Candidates">
        <div className="space-y-2">
          {result.root_cause_candidates.map((candidate) => (
            <article key={candidate.title} className="rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge className={groundingClass(candidate.grounding)}>{candidate.grounding}</Badge>
                {candidate.supporting_evidence.map((ref) => (
                  <Badge key={ref} className="border-slate-200/10 bg-slate-200/[0.04] text-slate-300/90">{ref}</Badge>
                ))}
              </div>
              <p className="text-sm font-semibold text-slate-100">{candidate.title}</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">{candidate.explanation}</p>
            </article>
          ))}
        </div>
      </PanelBlock>
      <PanelBlock title="Blast Radius">
        <p className="text-sm leading-6 text-slate-300">{result.blast_radius}</p>
        <p className="mt-2 text-xs leading-5 text-slate-500">{result.evidence_summary}</p>
      </PanelBlock>
      <PanelBlock title="Prevention Actions">
        <div className="space-y-2">
          {result.prevention_actions.map((action) => (
            <article key={action.action} className="rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge className={severityClass(action.priority)}>{action.priority}</Badge>
                {action.related_evidence.map((ref) => (
                  <Badge key={ref} className="border-slate-200/10 bg-slate-200/[0.04] text-slate-300/90">{ref}</Badge>
                ))}
              </div>
              <p className="text-sm font-semibold text-slate-100">{action.action}</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">{action.rationale}</p>
            </article>
          ))}
        </div>
      </PanelBlock>
      <PanelBlock title="Grounding And Limits">
        <p className="text-sm leading-6 text-slate-300">{result.grounding_notes}</p>
        <ul className="mt-3 space-y-1 text-xs leading-5 text-slate-500">
          {result.analysis_limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </PanelBlock>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: "red" | "amber" | "cyan" | "green" }) {
  const iconClass =
    tone === "red"
      ? "text-red-200/80"
      : tone === "amber"
        ? "text-amber-100/80"
        : tone === "cyan"
          ? "text-cyan-100/80"
          : "text-emerald-100/80";
  return (
    <div className="rounded-2xl border border-white/[0.07] bg-[hsl(var(--surface-elevated))] p-4 shadow-[0_8px_20px_rgba(0,0,0,0.09)]">
      <div className="mb-2 flex items-center gap-2 text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {tone === "red" ? <AlertTriangle className={`h-3.5 w-3.5 ${iconClass}`} /> : tone === "green" ? <CheckCircle2 className={`h-3.5 w-3.5 ${iconClass}`} /> : tone === "cyan" ? <Network className={`h-3.5 w-3.5 ${iconClass}`} /> : <Database className={`h-3.5 w-3.5 ${iconClass}`} />}
        {label}
      </div>
      <p className="text-lg font-semibold text-slate-100">{value}</p>
    </div>
  );
}

function PanelBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-white/[0.07] bg-[hsl(var(--surface-elevated))] p-5 shadow-[0_8px_20px_rgba(0,0,0,0.09)]">
      <h3 className="mb-3 text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</h3>
      {children}
    </section>
  );
}
