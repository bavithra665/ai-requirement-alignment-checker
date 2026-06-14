"use client";

import { useEffect, useState, useCallback } from "react";
import { api, Project, ProjectHealth, MismatchReport } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  ShieldAlert,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Activity,
  Target,
  TrendingUp,
  Shield,
  HeartPulse,
  Layers,
  Bug,
  FileCheck,
} from "lucide-react";

// ─── Animated Number ──────────────────────────────────────────────────────────

function AnimatedNumber({ value, duration = 800 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const start = performance.now();
    const from = 0;
    const to = value;
    function step(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(from + (to - from) * eased));
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }, [value, duration]);
  return <>{display}</>;
}

// ─── Health Score Ring (SVG) ──────────────────────────────────────────────────

function HealthScoreRing({ score, status }: { score: number; status: string }) {
  const radius = 80;
  const stroke = 10;
  const normalizedRadius = radius - stroke;
  const circumference = 2 * Math.PI * normalizedRadius;
  const offset = circumference - (score / 100) * circumference;

  const colorMap: Record<string, { stroke: string; text: string; bg: string; glow: string }> = {
    Excellent: { stroke: "#10b981", text: "text-emerald-600", bg: "from-emerald-50 to-emerald-100/50", glow: "shadow-emerald-200/50" },
    Good: { stroke: "#f59e0b", text: "text-amber-600", bg: "from-amber-50 to-amber-100/50", glow: "shadow-amber-200/50" },
    "Needs Attention": { stroke: "#f97316", text: "text-orange-600", bg: "from-orange-50 to-orange-100/50", glow: "shadow-orange-200/50" },
    Critical: { stroke: "#ef4444", text: "text-red-600", bg: "from-red-50 to-red-100/50", glow: "shadow-red-200/50" },
  };

  const colors = colorMap[status] || colorMap["Good"];

  return (
    <Card className={`glass border border-white/30 bg-gradient-to-br ${colors.bg} shadow-lg ${colors.glow}`}>
      <CardContent className="py-8 flex flex-col items-center justify-center">
        <div className="relative">
          <svg width={radius * 2} height={radius * 2} className="transform -rotate-90">
            {/* Background track */}
            <circle
              cx={radius}
              cy={radius}
              r={normalizedRadius}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth={stroke}
              opacity={0.4}
            />
            {/* Score arc */}
            <circle
              cx={radius}
              cy={radius}
              r={normalizedRadius}
              fill="none"
              stroke={colors.stroke}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-all duration-1000 ease-out"
              style={{ filter: `drop-shadow(0 0 6px ${colors.stroke}40)` }}
            />
          </svg>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-black ${colors.text}`}>
              <AnimatedNumber value={score} duration={1200} />
            </span>
            <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mt-0.5">
              Health Score
            </span>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2">
          <HeartPulse className={`h-4 w-4 ${colors.text}`} />
          <Badge className={`${
            status === "Excellent" ? "bg-emerald-100 text-emerald-700 border-emerald-200" :
            status === "Good" ? "bg-amber-100 text-amber-700 border-amber-200" :
            status === "Needs Attention" ? "bg-orange-100 text-orange-700 border-orange-200" :
            "bg-red-100 text-red-700 border-red-200"
          } border text-sm font-bold px-3 py-1`}>
            {status}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Alignment Distribution Bar ───────────────────────────────────────────────

function AlignmentDistribution({
  aligned,
  drift,
  misaligned,
  total,
}: {
  aligned: number;
  drift: number;
  misaligned: number;
  total: number;
}) {
  if (total === 0) return null;
  const alignedPct = (aligned / total) * 100;
  const driftPct = (drift / total) * 100;
  const misalignedPct = (misaligned / total) * 100;

  return (
    <Card className="glass border border-white/20">
      <CardContent className="py-6">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="h-4 w-4 text-[#0096C7]" />
          <h3 className="text-sm font-semibold text-foreground">Alignment Distribution</h3>
        </div>

        {/* Stacked bar */}
        <div className="h-8 rounded-full overflow-hidden flex bg-gray-100 shadow-inner">
          {alignedPct > 0 && (
            <div
              className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-1000 ease-out flex items-center justify-center"
              style={{ width: `${alignedPct}%` }}
            >
              {alignedPct > 12 && (
                <span className="text-[10px] font-bold text-white drop-shadow-sm">
                  {Math.round(alignedPct)}%
                </span>
              )}
            </div>
          )}
          {driftPct > 0 && (
            <div
              className="h-full bg-gradient-to-r from-amber-400 to-amber-500 transition-all duration-1000 ease-out flex items-center justify-center"
              style={{ width: `${driftPct}%` }}
            >
              {driftPct > 12 && (
                <span className="text-[10px] font-bold text-white drop-shadow-sm">
                  {Math.round(driftPct)}%
                </span>
              )}
            </div>
          )}
          {misalignedPct > 0 && (
            <div
              className="h-full bg-gradient-to-r from-red-400 to-red-500 transition-all duration-1000 ease-out flex items-center justify-center"
              style={{ width: `${misalignedPct}%` }}
            >
              {misalignedPct > 12 && (
                <span className="text-[10px] font-bold text-white drop-shadow-sm">
                  {Math.round(misalignedPct)}%
                </span>
              )}
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-6 mt-4 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-muted-foreground">Aligned</span>
            <span className="font-bold text-emerald-600">{aligned}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span className="text-muted-foreground">Drift</span>
            <span className="font-bold text-amber-600">{drift}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-muted-foreground">Misaligned</span>
            <span className="font-bold text-red-600">{misaligned}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Health Factors ───────────────────────────────────────────────────────────

function HealthFactors({ health }: { health: ProjectHealth }) {
  const factors = [
    {
      label: "Alignment Rate",
      value: health.aligned_count + health.drift_count + health.misaligned_count > 0
        ? Math.round((health.aligned_count / (health.aligned_count + health.drift_count + health.misaligned_count)) * 100)
        : 0,
      icon: <Target className="h-4 w-4 text-emerald-500" />,
      color: "bg-emerald-500",
    },
    {
      label: "Avg Alignment Score",
      value: Math.round(health.avg_alignment_score),
      icon: <TrendingUp className="h-4 w-4 text-[#0096C7]" />,
      color: "bg-[#0096C7]",
    },
    {
      label: "Issue Resolution",
      value: health.open_mismatches + health.resolved_mismatches > 0
        ? Math.round((health.resolved_mismatches / (health.open_mismatches + health.resolved_mismatches)) * 100)
        : 100,
      icon: <Shield className="h-4 w-4 text-violet-500" />,
      color: "bg-violet-500",
    },
    {
      label: "Requirement Coverage",
      value: health.total_requirements > 0
        ? Math.round((health.approved_requirements / health.total_requirements) * 100)
        : 0,
      icon: <FileCheck className="h-4 w-4 text-amber-500" />,
      color: "bg-amber-500",
    },
  ];

  return (
    <Card className="glass border border-white/20">
      <CardContent className="py-6">
        <div className="flex items-center gap-2 mb-5">
          <Activity className="h-4 w-4 text-[#0096C7]" />
          <h3 className="text-sm font-semibold text-foreground">Health Factors</h3>
        </div>

        <div className="space-y-4">
          {factors.map((f) => (
            <div key={f.label} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  {f.icon}
                  <span className="text-muted-foreground font-medium">{f.label}</span>
                </div>
                <span className="font-bold text-foreground">{f.value}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ease-out ${f.color}`}
                  style={{ width: `${f.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Risk Breakdown Cards ─────────────────────────────────────────────────────

function RiskBreakdown({ reports }: { reports: MismatchReport[] }) {
  const critical = reports.filter((r) => r.severity === "Critical").length;
  const high = reports.filter((r) => r.severity === "High").length;
  const medium = reports.filter((r) => r.severity === "Medium").length;
  const low = reports.filter((r) => r.severity === "Low").length;

  const items = [
    { label: "Critical", count: critical, color: "text-red-600", bg: "bg-red-50/60", border: "border-red-200", dot: "bg-red-500", icon: <XCircle className="h-5 w-5 text-red-500" /> },
    { label: "High", count: high, color: "text-orange-600", bg: "bg-orange-50/60", border: "border-orange-200", dot: "bg-orange-500", icon: <AlertTriangle className="h-5 w-5 text-orange-500" /> },
    { label: "Medium", count: medium, color: "text-amber-600", bg: "bg-amber-50/60", border: "border-amber-200", dot: "bg-amber-500", icon: <Bug className="h-5 w-5 text-amber-500" /> },
    { label: "Low", count: low, color: "text-green-600", bg: "bg-green-50/60", border: "border-green-200", dot: "bg-green-500", icon: <CheckCircle2 className="h-5 w-5 text-green-500" /> },
  ];

  return (
    <Card className="glass border border-white/20">
      <CardContent className="py-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldAlert className="h-4 w-4 text-amber-500" />
          <h3 className="text-sm font-semibold text-foreground">Risk Breakdown</h3>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {items.map((item) => (
            <div
              key={item.label}
              className={`rounded-xl ${item.bg} border ${item.border} p-4 text-center transition-all duration-300 hover:shadow-md hover:scale-[1.02]`}
            >
              <div className="flex justify-center mb-2">{item.icon}</div>
              <div className={`text-2xl font-black ${item.color}`}>
                <AnimatedNumber value={item.count} />
              </div>
              <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mt-1">
                {item.label}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Drift Trend Snapshot ─────────────────────────────────────────────────────

function DriftSnapshot({ health }: { health: ProjectHealth }) {
  return (
    <Card className="glass border border-white/20">
      <CardContent className="py-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-4 w-4 text-[#48CAE4]" />
          <h3 className="text-sm font-semibold text-foreground">Current Drift Snapshot</h3>
        </div>

        <div className="flex items-center justify-center py-6">
          {/* SVG mini-gauge for drift percentage */}
          <div className="relative">
            <svg width="120" height="120" className="transform -rotate-90">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="8" opacity={0.3} />
              <circle
                cx="60"
                cy="60"
                r="50"
                fill="none"
                stroke={health.drift_percentage > 30 ? "#ef4444" : health.drift_percentage > 15 ? "#f59e0b" : "#10b981"}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 50}
                strokeDashoffset={2 * Math.PI * 50 * (1 - health.drift_percentage / 100)}
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-2xl font-black ${
                health.drift_percentage > 30 ? "text-red-600" : health.drift_percentage > 15 ? "text-amber-600" : "text-emerald-600"
              }`}>
                {Math.round(health.drift_percentage)}%
              </span>
              <span className="text-[10px] text-muted-foreground font-semibold uppercase">Drift Rate</span>
            </div>
          </div>
        </div>

        <div className="text-center text-xs text-muted-foreground">
          <p>
            {health.drift_percentage <= 10
              ? "✅ Excellent — minimal drift detected"
              : health.drift_percentage <= 25
              ? "⚡ Moderate — some requirements drifting"
              : "🚨 High — significant drift, action needed"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function RiskDashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [health, setHealth] = useState<ProjectHealth | null>(null);
  const [mismatches, setMismatches] = useState<MismatchReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const projList = await api.getProjects();
        setProjects(projList);
        if (projList.length > 0) {
          setSelectedProjectId(projList[0].id);
        }
      } catch {
        setError("Failed to load projects.");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  const loadData = useCallback(async () => {
    if (!selectedProjectId) {
      setHealth(null);
      setMismatches([]);
      return;
    }
    setDataLoading(true);
    setError(null);
    try {
      const [h, m] = await Promise.all([
        api.getProjectHealth(selectedProjectId),
        api.getMismatchReports(selectedProjectId),
      ]);
      setHealth(h);
      setMismatches(m);
    } catch {
      setHealth(null);
      setMismatches([]);
    } finally {
      setDataLoading(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-24">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground text-sm">Loading risk dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with gradient */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-6 md:p-8 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="h-6 w-6 text-red-400" />
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
                Risk Dashboard
              </h1>
            </div>
            <p className="text-slate-300 text-sm">
              Real-time project health monitoring, alignment insights, and risk assessment
            </p>
          </div>

          <select
            id="risk-project-selector"
            className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg px-3 py-2 text-sm text-white focus:ring-2 focus:ring-[#48CAE4] outline-none"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            <option value="" className="text-gray-900">— Select Project —</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id} className="text-gray-900">{p.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {dataLoading ? (
        <div className="flex flex-col items-center justify-center p-16">
          <Loader2 className="h-10 w-10 animate-spin text-primary mb-3" />
          <p className="text-muted-foreground text-sm">Loading health data...</p>
        </div>
      ) : !health ? (
        <Card className="glass border border-white/20">
          <CardContent className="py-16 flex flex-col items-center justify-center gap-3 text-muted-foreground">
            <BarChart3 className="h-14 w-14 text-muted-foreground/20" />
            <div className="text-center">
              <p className="font-semibold">No health data available</p>
              <p className="text-sm mt-1">
                To view risk insights:
                <br />✓ Select a project with alignment results
                <br />✓ Run alignment analysis first
                <br />✓ Generate mismatch reports for full risk assessment
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { label: "Requirements", value: health.total_requirements, icon: <FileCheck className="h-4 w-4 text-[#0096C7]" />, color: "text-[#0096C7]" },
              { label: "Aligned", value: health.aligned_count, icon: <CheckCircle2 className="h-4 w-4 text-emerald-500" />, color: "text-emerald-600" },
              { label: "Drift", value: health.drift_count, icon: <AlertTriangle className="h-4 w-4 text-amber-500" />, color: "text-amber-600" },
              { label: "Misaligned", value: health.misaligned_count, icon: <XCircle className="h-4 w-4 text-red-500" />, color: "text-red-600" },
              { label: "Open Issues", value: health.open_mismatches, icon: <Bug className="h-4 w-4 text-red-500" />, color: "text-red-600" },
              { label: "Resolved", value: health.resolved_mismatches, icon: <Shield className="h-4 w-4 text-emerald-500" />, color: "text-emerald-600" },
            ].map((kpi) => (
              <Card key={kpi.label} className="glass border border-white/20 hover:shadow-md transition-all duration-300 hover:scale-[1.02]">
                <CardContent className="pt-4 pb-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    {kpi.icon}
                    <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">
                      {kpi.label}
                    </span>
                  </div>
                  <div className={`text-2xl font-black ${kpi.color}`}>
                    <AnimatedNumber value={kpi.value} />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Main Grid: Health Ring + Distribution */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Health Score Ring */}
            <HealthScoreRing score={health.health_score} status={health.health_status} />

            {/* Alignment Distribution + Drift Snapshot */}
            <div className="lg:col-span-2 space-y-6">
              <AlignmentDistribution
                aligned={health.aligned_count}
                drift={health.drift_count}
                misaligned={health.misaligned_count}
                total={health.aligned_count + health.drift_count + health.misaligned_count}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <DriftSnapshot health={health} />
                <HealthFactors health={health} />
              </div>
            </div>
          </div>

          {/* Risk Breakdown */}
          <RiskBreakdown reports={mismatches} />
        </>
      )}
    </div>
  );
}
