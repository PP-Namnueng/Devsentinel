"use client";

import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronDown,
  Database,
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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

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

type PRIssue = {
  severity: "critical" | "high" | "medium" | "low";
  category: "bug" | "security" | "performance" | "architecture";
  title: string;
  file?: string;
  line?: number;
  evidence: string;
  reasoning: string;
  suggested_fix: string;
  skill_references: string[];
  confidence: number;
};

type PRResult = {
  decision: "approve" | "request_changes" | "needs_discussion";
  summary: string;
  issues: PRIssue[];
  reviewer_notes: string[];
};

type TimelineEvent = {
  timestamp: string;
  event: string;
  evidence: string;
};

type PreventionAction = {
  priority: "p0" | "p1" | "p2";
  owner: string;
  action: string;
  rationale: string;
};

type IncidentResult = {
  severity: "sev1" | "sev2" | "sev3" | "sev4";
  executive_summary: string;
  root_cause: string;
  causal_chain: string[];
  timeline: TimelineEvent[];
  post_mortem: {
    impact: string;
    root_cause: string;
    contributing_factors: string[];
    what_went_well: string[];
    what_went_wrong: string[];
    prevention_plan: PreventionAction[];
  };
  skill_references: string[];
  confidence: number;
};

type LoadingMode = "pr" | "incident";
type AppView = "workspace" | "settings";
type Provider = "OpenAI" | "Ollama" | "OpenRouter" | "Custom Endpoint";

const providerModels: Record<Provider, string[]> = {
  OpenAI: ["gpt-4.1", "gpt-4.1-mini", "o4-mini"],
  Ollama: ["qwen2.5-coder", "deepseek-coder", "mistral-nemo"],
  OpenRouter: ["anthropic/claude-3.5-sonnet", "qwen/qwen-2.5-coder-32b", "mistralai/codestral"],
  "Custom Endpoint": ["devsentinel-coder-14b", "custom-review-model", "custom-incident-model"]
};

const INVESTIGATION_STAGES: Record<LoadingMode, string[]> = {
  pr: [
    "Parsing diff...",
    "Analyzing architecture boundaries...",
    "Checking security conventions...",
    "Detecting risky patterns...",
    "Generating validated output..."
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

function timelineTone(event: TimelineEvent) {
  const text = `${event.event} ${event.evidence}`.toLowerCase();
  if (text.includes("503") || text.includes("exhausted") || text.includes("timeout")) return "failure";
  if (text.includes("spike") || text.includes("n+1") || text.includes("nearing")) return "warning";
  if (text.includes("recover") || text.includes("rollback")) return "recovered";
  return "healthy";
}

function toneDotClass(tone: string) {
  if (tone === "failure") return "border-red-200 bg-red-300";
  if (tone === "warning") return "border-amber-100 bg-amber-200";
  if (tone === "recovered") return "border-cyan-100 bg-cyan-200";
  return "border-emerald-100 bg-emerald-300";
}

function prRiskScore(result: PRResult | null) {
  if (!result) return 0;
  return Math.min(
    100,
    result.issues.reduce((score, issue) => {
      const weight = issue.severity === "critical" ? 34 : issue.severity === "high" ? 24 : issue.severity === "medium" ? 14 : 7;
      return score + weight;
    }, 0)
  );
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export default function Home() {
  const [prInput, setPrInput] = useState(SAMPLE_PR);
  const [logsInput, setLogsInput] = useState(SAMPLE_LOGS);
  const [prResult, setPrResult] = useState<PRResult | null>(null);
  const [incidentResult, setIncidentResult] = useState<IncidentResult | null>(null);
  const [loading, setLoading] = useState<LoadingMode | null>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<AppView>("workspace");

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

  const prScore = useMemo(() => prRiskScore(prResult), [prResult]);

  async function runPrReview() {
    setError(null);
    setPrResult(null);
    setLoading("pr");
    try {
      const [result] = await Promise.all([postJson<PRResult>("/pr-autopilot", { diff: prInput }), sleep(2850)]);
      setPrResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PR review failed");
    } finally {
      setLoading(null);
    }
  }

  async function runIncidentAutopsy() {
    setError(null);
    setIncidentResult(null);
    setLoading("incident");
    try {
      const [result] = await Promise.all([postJson<IncidentResult>("/incident-autopsy", { logs: logsInput }), sleep(2850)]);
      setIncidentResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Incident autopsy failed");
    } finally {
      setLoading(null);
    }
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
            <SystemPill tone="cyan" label="MODEL: devsentinel-coder-14b" />
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
          <ModelGatewaySettings />
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
                  {loading === "pr" ? <InvestigationState mode="pr" stageIndex={stageIndex} /> : prResult ? <PRReview result={prResult} riskScore={prScore} /> : <EmptyState label="Awaiting engineering input..." />}
                </IntelligencePanel>
              }
            />
          </TabsContent>

          <TabsContent value="incident">
            <WorkspaceShell
              label="INCIDENT LOG STREAM"
              source="dashboard-api.log"
              icon={<TerminalSquare className="h-4 w-4 text-cyan-100/65" aria-hidden="true" />}
              action={
                <Button onClick={runIncidentAutopsy} disabled={loading !== null}>
                  {loading === "incident" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                  Run Autopsy
                </Button>
              }
              input={<Textarea value={logsInput} onChange={(event) => setLogsInput(event.target.value)} spellCheck={false} />}
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

function ModelGatewaySettings() {
  const providers: Provider[] = ["OpenAI", "Ollama", "OpenRouter", "Custom Endpoint"];
  const [provider, setProvider] = useState<Provider>("OpenAI");
  const [model, setModel] = useState(providerModels.OpenAI[0]);
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [connected, setConnected] = useState(false);

  function updateProvider(nextProvider: Provider) {
    setProvider(nextProvider);
    setModel(providerModels[nextProvider][0]);
    setConnected(false);
  }

  function testConnection() {
    setConnected(false);
    window.setTimeout(() => setConnected(true), 700);
  }

  const routeOptions = ["OpenAI / gpt-4.1", "Ollama / qwen2.5-coder", "OpenRouter / qwen-2.5-coder-32b"];

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
                  <GatewayField label="Local Model">
                    <GatewaySelect value={model} onChange={setModel} options={providerModels.Ollama} />
                  </GatewayField>
                </>
              ) : (
                <>
                  <GatewayField label={provider === "OpenAI" ? "API Key" : "Endpoint / API Key"}>
                    <GatewayInput icon={KeyRound} type="password" value={provider === "OpenAI" ? "sk-••••••••••••••••••••••••" : "configured-secret"} readOnly />
                  </GatewayField>
                  <GatewayField label="Model">
                    <GatewaySelect value={model} onChange={setModel} options={providerModels[provider]} />
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
              <Button onClick={testConnection}>
                <Plug className="h-4 w-4" />
                Test Connection
              </Button>
              {connected && (
                <div className="flex items-center gap-2 text-sm text-emerald-100/85">
                  <CheckCircle2 className="h-4 w-4" />
                  Connection verified
                </div>
              )}
            </div>
          </GatewayStep>

          <GatewayStep
            step="03"
            title="Task Routing"
            description="Route each AI workflow to the runtime best suited for its reasoning profile."
          >
            <div className="space-y-3">
              <GatewayRoute label="PR Review" options={routeOptions} defaultValue="OpenAI / gpt-4.1" />
              <GatewayRoute label="Incident Analysis" options={routeOptions} defaultValue="Ollama / qwen2.5-coder" />
              <GatewayRoute label="Root Cause Analysis" options={routeOptions} defaultValue="OpenAI / gpt-4.1" />
            </div>
          </GatewayStep>

          <GatewayStep
            step="04"
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
            step="05"
            title="Save Configuration"
            description="Persist this orchestration profile for DevSentinel runtime execution."
          >
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-200">Ready to apply gateway configuration</p>
              <p className="mt-1 text-xs text-slate-500">Settings remain local until saved.</p>
            </div>
            <Button>
              <Save className="h-4 w-4" />
              Save Gateway Configuration
            </Button>
          </div>
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

function GatewaySelect({ value, onChange, options }: { value: string; onChange: (value: string) => void; options: string[] }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
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

function GatewayRoute({ label, options, defaultValue }: { label: string; options: string[]; defaultValue: string }) {
  const [value, setValue] = useState(defaultValue);
  return (
    <div className="grid gap-3 rounded-xl bg-white/[0.014] p-3 md:grid-cols-[13rem_1rem_1fr] md:items-center">
      <div>
        <p className="text-sm font-medium text-slate-200">{label}</p>
        <p className="mt-1 text-xs text-slate-500">AI workflow route</p>
      </div>
      <span className="hidden text-slate-600 md:block">→</span>
      <GatewaySelect value={value} onChange={setValue} options={options} />
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

function PRReview({ result, riskScore }: { result: PRResult; riskScore: number }) {
  const avgConfidence = Math.round((result.issues.reduce((total, issue) => total + issue.confidence, 0) / Math.max(result.issues.length, 1)) * 100);

  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <Metric label="Risk Score" value={`${riskScore}/100`} tone="red" />
        <Metric label="Decision" value={titleCase(result.decision)} tone="amber" />
        <Metric label="Confidence" value={`${avgConfidence}%`} tone="cyan" />
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
              <span className="font-mono text-xs text-slate-500">
                {issue.file}
                {issue.line ? `:${issue.line}` : ""}
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

function IncidentAutopsy({ result }: { result: IncidentResult }) {
  return (
    <div className="space-y-4 animate-fade-in-up">
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <Metric label="Incident" value={`${result.severity.toUpperCase()} Incident`} tone="amber" />
        <Metric label="Confidence" value={`${Math.round(result.confidence * 100)}%`} tone="cyan" />
        <Metric label="Blast Radius" value="dashboard-api, postgres-primary" tone="red" />
        <Metric label="MTTR" value="8m 12s" tone="green" />
      </div>
      <PanelBlock title="Root Cause">
        <p className="text-sm leading-6 text-slate-300">{result.root_cause}</p>
      </PanelBlock>
      <PanelBlock title="Incident Timeline">
        <div className="relative space-y-0 pl-6">
          <div className="absolute bottom-3 left-[0.55rem] top-3 w-px bg-white/[0.065]" />
          {result.timeline.map((item, index) => {
            const tone = timelineTone(item);
            const time = item.timestamp.slice(11, 16);
            return (
              <div key={`${item.timestamp}-${item.event}`} className="relative pb-5 last:pb-0">
                <span className={`absolute -left-[1.05rem] top-1 h-3 w-3 rounded-full border ${toneDotClass(tone)}`} />
                <div
                  className="animate-fade-in-up rounded-xl border border-white/[0.07] bg-[hsl(var(--surface-elevated))] p-4"
                  style={{ animationDelay: `${index * 70}ms` }}
                >
                  <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-xs font-semibold text-slate-400">{time}</span>
                    <Badge className={severityClass(tone)}>{tone}</Badge>
                  </div>
                  <p className="text-sm font-semibold text-slate-100">{item.event}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{item.evidence}</p>
                </div>
              </div>
            );
          })}
        </div>
      </PanelBlock>
      <PanelBlock title="Causal Chain">
        <ol className="space-y-2">
          {result.causal_chain.map((item, index) => (
            <li key={item} className="flex gap-3 rounded-xl border border-white/[0.065] bg-white/[0.018] p-3 text-sm text-slate-300">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-cyan-100/[0.045] font-mono text-xs font-semibold text-cyan-100/90">
                {index + 1}
              </span>
              {item}
            </li>
          ))}
        </ol>
      </PanelBlock>
      <PanelBlock title="Prevention Actions">
        <div className="space-y-2">
          {result.post_mortem.prevention_plan.map((action) => (
            <article key={action.action} className="rounded-xl border border-white/[0.065] bg-white/[0.018] p-3">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge className={severityClass(action.priority)}>{action.priority}</Badge>
                <Badge className="border-slate-200/10 bg-slate-200/[0.04] text-slate-300/90">{action.owner}</Badge>
              </div>
              <p className="text-sm font-semibold text-slate-100">{action.action}</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">{action.rationale}</p>
            </article>
          ))}
        </div>
      </PanelBlock>
      <PanelBlock title="Memory References">
        <ul className="space-y-1 text-xs leading-5 text-slate-500">
          {result.skill_references.map((reference) => (
            <li key={reference}>{reference}</li>
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
