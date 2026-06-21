"use client";
/* eslint-disable react-hooks/exhaustive-deps */

import { useEffect, useState } from "react";
import { api, Project, AlignmentResult } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  Zap,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  GitMerge,
  ArrowDown,
  Cpu,
  FileText,
  MessageSquare,
} from "lucide-react";

// ─── Helper utilities ─────────────────────────────────────────────────────────

function statusColor(status: string) {
  switch (status) {
    case "Aligned":        return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "Potential Drift": return "bg-amber-100 text-amber-800 border-amber-200";
    case "Misaligned":     return "bg-red-100 text-red-800 border-red-200";
    default:               return "bg-gray-100 text-gray-700";
  }
}

function statusIcon(status: string) {
  switch (status) {
    case "Aligned":        return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
    case "Potential Drift": return <AlertTriangle className="h-4 w-4 text-amber-500" />;
    case "Misaligned":     return <XCircle className="h-4 w-4 text-red-500" />;
    default:               return null;
  }
}

function scoreBar(score: number | undefined, label: string) {
  if (score === undefined || score === null) {
    return (
      <div className="space-y-1">
        <div className="flex justify-between items-center text-xs">
          <span className="text-muted-foreground">{label}</span>
          <span className="text-muted-foreground/50 italic text-[10px]">N/A</span>
        </div>
        <div className="h-1.5 bg-muted/30 rounded-full" />
      </div>
    );
  }
  const color = score >= 75 ? "bg-emerald-500" : score >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={`font-bold ${score >= 75 ? "text-emerald-600" : score >= 50 ? "text-amber-600" : "text-red-600"}`}>
          {score}%
        </span>
      </div>
      <div className="h-1.5 bg-muted/30 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

// ─── Alignment Chain Row ──────────────────────────────────────────────────────

function AlignmentRow({ result }: { result: AlignmentResult }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`border rounded-xl overflow-hidden transition-all duration-300 bg-white shadow-sm ${
      result.alignment_status === "Misaligned"
        ? "border-red-200"
        : result.alignment_status === "Potential Drift"
        ? "border-amber-200"
        : "border-emerald-100"
    }`}>
      {/* Header Row */}
      <div
        className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-muted/5 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 min-w-0">
          {statusIcon(result.alignment_status)}
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground break-words pr-4">
              {result.requirement_title || `Requirement Version — Alignment #${result.id.slice(0, 8)}`}
            </p>
            <p className="text-xs text-muted-foreground">
              Confidence: {result.confidence}%
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 shrink-0">
          {/* Overall Score Pill */}
          <div className="text-center">
            <div className={`text-2xl font-black ${
              result.overall_alignment_score >= 75 ? "text-emerald-600" :
              result.overall_alignment_score >= 50 ? "text-amber-600" : "text-red-600"
            }`}>
              {result.overall_alignment_score}%
            </div>
            <div className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">
              Overall
            </div>
          </div>

          <Badge className={`${statusColor(result.alignment_status)} border text-xs font-semibold px-3 py-1`}>
            {result.alignment_status}
          </Badge>

          {expanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t px-5 py-5 space-y-5 bg-muted/5">
          {/* Traceability Chain Visualization */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Traceability Chain
            </h4>
            <div className="flex flex-col gap-1 items-start">
              {/* Requirement node */}
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 border border-blue-100 w-full">
                <FileText className="h-4 w-4 text-blue-500 shrink-0" />
                <span className="text-xs font-semibold text-blue-700">
                  Approved Baseline Requirement
                </span>
                <Badge className="ml-auto bg-blue-100 text-blue-700 text-[10px]">Baseline</Badge>
              </div>

              {/* Arrow + score */}
              <div className="flex flex-col items-center ml-4 my-0.5 gap-0.5">
                <ArrowDown className="h-3.5 w-3.5 text-muted-foreground/50" />
                {result.requirement_jira_score !== undefined && result.requirement_jira_score !== null && (
                  <span className={`text-[10px] font-bold ${
                    result.requirement_jira_score >= 75 ? "text-emerald-600" :
                    result.requirement_jira_score >= 50 ? "text-amber-600" : "text-red-600"
                  }`}>
                    {result.requirement_jira_score}% match
                  </span>
                )}
              </div>

              {/* Jira Story node */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border w-full ${
                result.jira_story_title ? "bg-sky-50 border-sky-100" : "bg-muted/30 border-dashed border-muted-foreground/20"
              }`}>
                <GitMerge className={`h-4 w-4 shrink-0 ${result.jira_story_title ? "text-sky-500" : "text-muted-foreground/30"}`} />
                <span className={`text-xs font-semibold ${result.jira_story_title ? "text-sky-700" : "text-muted-foreground/50"} break-words`}>
                  {result.jira_story_title ? result.jira_story_title : "No Jira Story Found"}
                </span>
                {result.requirement_jira_score !== undefined && result.requirement_jira_score !== null && (
                  <Badge className={`ml-auto text-[10px] ${
                    result.requirement_jira_score >= 75 ? "bg-emerald-100 text-emerald-700" :
                    result.requirement_jira_score >= 50 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
                  }`}>
                    {result.requirement_jira_score}%
                  </Badge>
                )}
              </div>

              {/* Arrow + score */}
              <div className="flex flex-col items-center ml-4 my-0.5 gap-0.5">
                <ArrowDown className="h-3.5 w-3.5 text-muted-foreground/50" />
                {result.jira_pr_score !== undefined && result.jira_pr_score !== null && (
                  <span className={`text-[10px] font-bold ${
                    result.jira_pr_score >= 75 ? "text-emerald-600" :
                    result.jira_pr_score >= 50 ? "text-amber-600" : "text-red-600"
                  }`}>
                    {result.jira_pr_score}% match
                  </span>
                )}
              </div>

              {/* Pull Request node */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border w-full ${
                result.pull_request_title ? "bg-violet-50 border-violet-100" : "bg-muted/30 border-dashed border-muted-foreground/20"
              }`}>
                <GitMerge className={`h-4 w-4 shrink-0 ${result.pull_request_title ? "text-violet-500" : "text-muted-foreground/30"}`} />
                <span className={`text-xs font-semibold ${result.pull_request_title ? "text-violet-700" : "text-muted-foreground/50"} break-words`}>
                  {result.pull_request_title ? result.pull_request_title : "No Pull Request Found"}
                </span>
                {result.jira_pr_score !== undefined && result.jira_pr_score !== null && (
                  <Badge className={`ml-auto text-[10px] ${
                    result.jira_pr_score >= 75 ? "bg-emerald-100 text-emerald-700" :
                    result.jira_pr_score >= 50 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
                  }`}>
                    {result.jira_pr_score}%
                  </Badge>
                )}
              </div>

              {/* Arrow + score */}
              <div className="flex flex-col items-center ml-4 my-0.5 gap-0.5">
                <ArrowDown className="h-3.5 w-3.5 text-muted-foreground/50" />
                {result.pr_artifact_score !== undefined && result.pr_artifact_score !== null && (
                  <span className={`text-[10px] font-bold ${
                    result.pr_artifact_score >= 75 ? "text-emerald-600" :
                    result.pr_artifact_score >= 50 ? "text-amber-600" : "text-red-600"
                  }`}>
                    {result.pr_artifact_score}% match
                  </span>
                )}
              </div>

              {/* Code Artifact node */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border w-full ${
                result.code_artifact_name ? "bg-teal-50 border-teal-100" : "bg-muted/30 border-dashed border-muted-foreground/20"
              }`}>
                <Cpu className={`h-4 w-4 shrink-0 ${result.code_artifact_name ? "text-teal-500" : "text-muted-foreground/30"}`} />
                <span className={`text-xs font-semibold ${result.code_artifact_name ? "text-teal-700" : "text-muted-foreground/50"} break-words`}>
                  {result.code_artifact_name ? result.code_artifact_name : "No Code Artifact Found"}
                </span>
                {result.pr_artifact_score !== undefined && result.pr_artifact_score !== null && (
                  <Badge className={`ml-auto text-[10px] ${
                    result.pr_artifact_score >= 75 ? "bg-emerald-100 text-emerald-700" :
                    result.pr_artifact_score >= 50 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
                  }`}>
                    {result.pr_artifact_score}%
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Score breakdown bars */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Chain Score Breakdown
            </h4>
            <div className="space-y-3">
              {scoreBar(result.requirement_jira_score, "Requirement → Jira Story")}
              {scoreBar(result.jira_pr_score, "Jira Story → Pull Request")}
              {scoreBar(result.pr_artifact_score, "Pull Request → Code Artifact")}
              <div className="pt-1 border-t">
                {scoreBar(result.overall_alignment_score, "Overall Weighted Score")}
              </div>
            </div>
          </div>

          {/* Groq AI Explanation */}
          {result.explanation && (
            <div className={`p-4 rounded-xl border ${
              result.alignment_status === "Misaligned"
                ? "bg-red-50/60 border-red-200"
                : result.alignment_status === "Potential Drift"
                ? "bg-amber-50/60 border-amber-200"
                : "bg-emerald-50/60 border-emerald-200"
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  AI Alignment Explanation
                </span>
                <Badge variant="outline" className="ml-auto text-[9px] py-0">Groq · Llama 3</Badge>
              </div>
              <p className="text-sm leading-relaxed text-foreground">{result.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AlignmentPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [results, setResults] = useState<AlignmentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRunInfo, setLastRunInfo] = useState<string | null>(null);

   
  useEffect(() => {
    async function init() {
      try {
        const projList = await api.getProjects();
        setProjects(projList);
        if (projList.length > 0) {
          setSelectedProjectId(projList[0].id);
        }
      } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
        console.warn(errMsg);
        setError("Failed to load projects.");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

   
   
   
  useEffect(() => {
    if (selectedProjectId) {
      loadResults();
    } else {
      setResults([]);
    }
  }, [selectedProjectId]);

  const loadResults = async () => {
    try {
      setError(null);
      const data = await api.getAlignmentResults(selectedProjectId);
      setResults(data);
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      setResults([]);
      console.warn("No alignment results found:", errMsg);
    }
  };

  const handleRunAlignment = async () => {
    if (!selectedProjectId) return;
    try {
      setRunning(true);
      setError(null);
      const res = await api.runAlignment(selectedProjectId);
      setLastRunInfo(`Analysis complete — ${res.results_generated} requirement chains evaluated.`);
      await loadResults();
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      setError(errMsg || "Alignment engine failed. Ensure backend is running and project has baseline requirements.");
    } finally {
      setRunning(false);
    }
  };

  // KPI counts
  const aligned = results.filter(r => r.alignment_status === "Aligned").length;
  const drift = results.filter(r => r.alignment_status === "Potential Drift").length;
  const misaligned = results.filter(r => r.alignment_status === "Misaligned").length;
  const avgScore = results.length > 0
    ? Math.round(results.reduce((sum, r) => sum + r.overall_alignment_score, 0) / results.length)
    : null;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-24">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground text-sm">Loading alignment workspace...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Zap className="h-6 w-6 text-amber-500" />
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              AI Alignment Engine
            </h1>
          </div>
          <p className="text-muted-foreground text-sm">
            Vector-based traceability analysis: Requirement → Jira → PR → Code Artifact
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            className="bg-white border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none shadow-sm"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            <option value="">— Select Project —</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>

          <Button
            onClick={handleRunAlignment}
            disabled={running || !selectedProjectId}
            className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-semibold shadow-md flex items-center gap-2"
          >
            {running ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Running Engine...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" /> Run Alignment Analysis
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Last run notification */}
      {lastRunInfo && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {lastRunInfo}
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {/* KPI Summary Cards */}
      {results.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="glass border border-white/20">
            <CardContent className="pt-5 pb-4">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                Avg Score
              </div>
              <div className={`text-3xl font-black ${
                (avgScore ?? 0) >= 75 ? "text-emerald-600" :
                (avgScore ?? 0) >= 50 ? "text-amber-600" : "text-red-600"
              }`}>
                {avgScore ?? "—"}%
              </div>
            </CardContent>
          </Card>

          <Card className="glass border border-emerald-100 bg-emerald-50/30">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-1.5 mb-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Aligned</span>
              </div>
              <div className="text-3xl font-black text-emerald-600">{aligned}</div>
            </CardContent>
          </Card>

          <Card className="glass border border-amber-100 bg-amber-50/30">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-1.5 mb-1">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Potential Drift</span>
              </div>
              <div className="text-3xl font-black text-amber-600">{drift}</div>
            </CardContent>
          </Card>

          <Card className="glass border border-red-100 bg-red-50/30">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-1.5 mb-1">
                <XCircle className="h-3.5 w-3.5 text-red-500" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Misaligned</span>
              </div>
              <div className="text-3xl font-black text-red-600">{misaligned}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-3">
        {running ? (
          <Card className="glass border border-white/20">
            <CardContent className="py-16 flex flex-col items-center justify-center gap-4">
              <div className="relative">
                <Zap className="h-14 w-14 text-amber-400 animate-pulse" />
                <Loader2 className="h-6 w-6 text-amber-600 animate-spin absolute -bottom-1 -right-1" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-foreground">Alignment Engine Running</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Generating embeddings → Computing chain similarities → Requesting AI explanations...
                </p>
              </div>
            </CardContent>
          </Card>
        ) : results.length === 0 ? (
          <Card className="glass border border-white/20">
            <CardContent className="py-16 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Zap className="h-14 w-14 text-muted-foreground/20" />
              <div className="text-center">
                <p className="font-semibold">No alignment results yet</p>
                <p className="text-sm mt-1">
                  Ensure the project has:
                  <br />✓ Approved baseline requirements
                  <br />✓ Synced Jira stories
                  <br />✓ Synced pull requests
                  <br />Then click <strong>Run Alignment Analysis</strong> above.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                {results.length} Requirement Traceability Record{results.length !== 1 ? "s" : ""}
              </h2>
              <span className="text-xs text-muted-foreground">Ordered by lowest alignment first</span>
            </div>
            {results.map((result) => (
              <AlignmentRow key={result.id} result={result} />
            ))}
          </>
        )}
      </div>
    </div>
  );
}
