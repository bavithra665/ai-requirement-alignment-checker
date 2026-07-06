"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { api, Project, MismatchReport } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Download,
  Eye,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Search,
  SlidersHorizontal,
  FileWarning,
  MessageSquareText,
  X,
} from "lucide-react";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function severityBadge(severity: string) {
  const map: Record<string, string> = {
    Critical: "bg-red-100 text-red-700 border-red-200",
    High: "bg-orange-100 text-orange-700 border-orange-200",
    Medium: "bg-amber-100 text-amber-700 border-amber-200",
    Low: "bg-green-100 text-green-700 border-green-200",
  };
  return map[severity] || "bg-gray-100 text-gray-700 border-gray-200";
}

function severityDot(severity: string) {
  const map: Record<string, string> = {
    Critical: "bg-red-500",
    High: "bg-orange-500",
    Medium: "bg-amber-500",
    Low: "bg-green-500",
  };
  return map[severity] || "bg-gray-400";
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    Open: "bg-red-50 text-red-700 border border-red-300",
    Reviewed: "bg-amber-50 text-amber-700 border border-amber-300",
    Resolved: "bg-emerald-50 text-emerald-700 border border-emerald-300",
  };
  return map[status] || "bg-gray-100 text-gray-700 border border-gray-200";
}

function statusIcon(status: string) {
  switch (status) {
    case "Open":
      return <XCircle className="h-3.5 w-3.5 text-red-500" />;
    case "Reviewed":
      return <Eye className="h-3.5 w-3.5 text-amber-500" />;
    case "Resolved":
      return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />;
    default:
      return null;
  }
}

// ─── Resolution Panel ─────────────────────────────────────────────────────────

function ResolutionPanel({
  mismatch,
  onClose,
  onSave,
}: {
  mismatch: MismatchReport;
  onClose: () => void;
  onSave: (id: string, data: { status?: string; resolution_notes?: string }) => Promise<void>;
}) {
  const [notes, setNotes] = useState(mismatch.resolution_notes || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async (newStatus: string) => {
    setSaving(true);
    await onSave(mismatch.id, { status: newStatus, resolution_notes: notes });
    setSaving(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
      <div className="w-full max-w-lg mx-4 bg-white rounded-2xl shadow-2xl border border-white/30 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full ${severityDot(mismatch.severity)}`} />
            <div>
              <h3 className="font-semibold text-foreground text-sm">Resolve Mismatch</h3>
              <p className="text-xs text-muted-foreground">{mismatch.mismatch_type}</p>
            </div>
          </div>
          <button
            id="resolution-close-btn"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-muted/80 transition-colors"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Description
            </label>
            <p className="text-sm text-foreground mt-1 leading-relaxed">{mismatch.description}</p>
          </div>

          {mismatch.suggested_fix && (
            <div className="p-3 rounded-xl bg-blue-50/60 border border-blue-100">
              <div className="flex items-center gap-1.5 mb-1">
                <Sparkles className="h-3.5 w-3.5 text-blue-500" />
                <span className="text-xs font-semibold text-blue-700">AI Suggested Fix</span>
              </div>
              <p className="text-sm text-blue-800 leading-relaxed">{mismatch.suggested_fix}</p>
            </div>
          )}

          <div>
            <label
              htmlFor="resolution-notes"
              className="text-xs font-semibold text-muted-foreground uppercase tracking-wider"
            >
              Resolution Notes
            </label>
            <textarea
              id="resolution-notes"
              className="mt-1.5 w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary/50 outline-none resize-none transition-all"
              rows={4}
              placeholder="Describe the resolution, actions taken, or reason for review..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-6 py-4 border-t bg-slate-50/50">
          <Button
            id="resolution-cancel-btn"
            variant="outline"
            onClick={onClose}
            className="text-sm"
          >
            Cancel
          </Button>
          <Button
            id="resolution-reviewed-btn"
            disabled={saving}
            onClick={() => handleSave("Reviewed")}
            className="bg-amber-500 hover:bg-amber-600 text-white text-sm"
          >
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <Eye className="h-3.5 w-3.5 mr-1" />}
            Mark Reviewed
          </Button>
          <Button
            id="resolution-resolve-btn"
            disabled={saving}
            onClick={() => handleSave("Resolved")}
            className="bg-emerald-500 hover:bg-emerald-600 text-white text-sm"
          >
            {saving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
            )}
            Resolve
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Mismatch Row ─────────────────────────────────────────────────────────────

function MismatchRow({
  report,
  onResolve,
}: {
  report: MismatchReport;
  onResolve: (m: MismatchReport) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`group border rounded-xl overflow-hidden transition-all duration-300 bg-white hover:shadow-md ${
        report.severity === "Critical"
          ? "border-red-200 hover:border-red-300"
          : report.severity === "High"
          ? "border-orange-200 hover:border-orange-300"
          : report.severity === "Medium"
          ? "border-amber-200 hover:border-amber-300"
          : "border-green-200 hover:border-green-300"
      }`}
    >
      {/* Header */}
      <div
        className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-muted/5 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Severity dot */}
        <div className={`w-3 h-3 rounded-full shrink-0 ring-4 ring-opacity-20 ${severityDot(report.severity)} ${
          report.severity === "Critical" ? "ring-red-200 animate-pulse" : 
          report.severity === "High" ? "ring-orange-200" : 
          report.severity === "Medium" ? "ring-amber-200" : "ring-green-200"
        }`} />

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <Badge className={`${severityBadge(report.severity)} text-[10px] font-bold uppercase tracking-wider border`}>
              {report.severity}
            </Badge>
            <span className="text-xs text-muted-foreground font-medium break-words">
              {report.requirement_title || `#${report.id.slice(0, 8)}`}
            </span>
          </div>
          <p className="text-sm font-medium text-foreground break-words">{report.mismatch_type}</p>
          <p className="text-xs text-muted-foreground break-words mt-0.5">
            {report.description}
          </p>
        </div>

        {/* Status + Actions */}
        <div className="flex items-center gap-3 shrink-0">
          <Badge className={`${statusBadge(report.status)} text-xs font-semibold px-2.5 py-0.5 flex items-center gap-1`}>
            {statusIcon(report.status)}
            {report.status}
          </Badge>

          {report.status !== "Resolved" && (
            <Button
              id={`resolve-btn-${report.id}`}
              variant="outline"
              size="sm"
              className="opacity-0 group-hover:opacity-100 transition-opacity text-xs"
              onClick={(e) => {
                e.stopPropagation();
                onResolve(report);
              }}
            >
              <MessageSquareText className="h-3.5 w-3.5 mr-1" />
              Resolve
            </Button>
          )}

          {expanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t px-5 py-4 bg-slate-50/50 space-y-3 animate-in slide-in-from-top-2 duration-200">
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Full Description
            </h4>
            <p className="text-sm text-foreground leading-relaxed">{report.description}</p>
          </div>

          {report.suggested_fix && (
            <div className="p-3 rounded-xl bg-blue-50/60 border border-blue-100">
              <div className="flex items-center gap-1.5 mb-1">
                <Sparkles className="h-3.5 w-3.5 text-blue-500" />
                <span className="text-xs font-semibold text-blue-700">AI Suggested Fix</span>
              </div>
              <p className="text-sm text-blue-800 leading-relaxed">{report.suggested_fix}</p>
            </div>
          )}

          {report.resolution_notes && (
            <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100">
              <div className="flex items-center gap-1.5 mb-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-xs font-semibold text-emerald-700">Resolution Notes</span>
              </div>
              <p className="text-sm text-emerald-800 leading-relaxed">{report.resolution_notes}</p>
            </div>
          )}

          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
            <span>Created: {new Date(report.created_at).toLocaleDateString()}</span>
            {report.reviewed_at && (
              <span>Reviewed: {new Date(report.reviewed_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function MismatchReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [reports, setReports] = useState<MismatchReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");

  // Resolution panel
  const [resolving, setResolving] = useState<MismatchReport | null>(null);

  const searchParams = useSearchParams();
  const projectParam = typeof searchParams?.get === "function" ? searchParams.get("projectId") : null;

  useEffect(() => {
    async function init() {
      try {
        const projList = await api.getProjects();
        setProjects(projList);

        // Determine initial project selection: URL param -> lastProjectId -> first project
        let initialId = "";
        if (projectParam && projList.some((p) => p.id === projectParam)) {
          initialId = projectParam;
        }

        if (!initialId && typeof window !== "undefined") {
          const last = localStorage.getItem("lastProjectId");
          if (last && projList.some((p) => p.id === last)) {
            initialId = last;
          }
        }

        if (!initialId && projList.length > 0) {
          initialId = projList[0].id;
        }

        setSelectedProjectId(initialId);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to load projects.";
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    init();
    // Intentionally run once on mount; deps include projectParam but searchParams is stable for initial mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadReports = useCallback(async () => {
    if (!selectedProjectId) {
      setReports([]);
      return;
    }
    try {
      setError(null);
      const data = await api.getMismatchReports(
        selectedProjectId,
        statusFilter || undefined,
        severityFilter || undefined
      );
      const scopedReports = data.filter((report) => report.project_id === selectedProjectId);
      setReports(scopedReports);
    } catch {
      setReports([]);
    }
  }, [selectedProjectId, statusFilter, severityFilter]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const handleGenerate = async () => {
    if (!selectedProjectId) return;
    try {
      setGenerating(true);
      setError(null);
      await api.generateMismatchReports(selectedProjectId);
      await loadReports();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to generate mismatch reports.";
      setError(message);
    } finally {
      setGenerating(false);
    }
  };

  const handleUpdateMismatch = async (id: string, data: { status?: string; resolution_notes?: string }) => {
    try {
      await api.updateMismatchReport(id, data);
      await loadReports();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update mismatch report.";
      setError(message);
    }
  };

  const handleExportCsv = async () => {
    if (!selectedProjectId) return;
    try {
      const blob = await api.exportMismatchesCsv(selectedProjectId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mismatches_${selectedProjectId.slice(0, 8)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to export CSV.");
    }
  };

  // KPI computation
  const total = reports.length;
  const openCount = reports.filter((r) => r.status === "Open").length;
  const reviewedCount = reports.filter((r) => r.status === "Reviewed").length;
  const resolvedCount = reports.filter((r) => r.status === "Resolved").length;
  const criticalCount = reports.filter((r) => r.severity === "Critical").length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-24">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground text-sm">Loading mismatch workspace...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Resolution Panel Modal */}
      {resolving && (
        <ResolutionPanel
          mismatch={resolving}
          onClose={() => setResolving(null)}
          onSave={handleUpdateMismatch}
        />
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className="h-6 w-6 text-amber-500" />
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Mismatch Reports
            </h1>
          </div>
          <p className="text-muted-foreground text-sm">
            AI-detected mismatches between requirements, stories, PRs, and code artifacts
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <select
            id="project-selector"
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
            id="generate-reports-btn"
            onClick={handleGenerate}
            disabled={generating || !selectedProjectId}
            className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-semibold shadow-md"
          >
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-1.5" /> Generate Reports
              </>
            )}
          </Button>

          <Button
            id="export-csv-btn"
            variant="outline"
            onClick={handleExportCsv}
            disabled={reports.length === 0}
            className="text-sm"
          >
            <Download className="h-4 w-4 mr-1.5" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <SlidersHorizontal className="h-3.5 w-3.5" />
          <span className="font-semibold uppercase tracking-wider">Filters</span>
        </div>
        <select
          id="status-filter"
          className="bg-white border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary outline-none"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Status</option>
          <option value="Open">Open</option>
          <option value="Reviewed">Reviewed</option>
          <option value="Resolved">Resolved</option>
        </select>
        <select
          id="severity-filter"
          className="bg-white border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary outline-none"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        >
          <option value="">All Severity</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        {(statusFilter || severityFilter) && (
          <button
            onClick={() => {
              setStatusFilter("");
              setSeverityFilter("");
            }}
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            <X className="h-3 w-3" /> Clear Filters
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {/* KPI Row */}
      {reports.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="glass border border-white/20">
            <CardContent className="pt-5 pb-4">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                Total
              </div>
              <div className="text-3xl font-black text-foreground">{total}</div>
            </CardContent>
          </Card>

          <Card className="glass border border-red-100 bg-red-50/30">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-1.5 mb-1">
                <XCircle className="h-3.5 w-3.5 text-red-500" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Open</span>
              </div>
              <div className="text-3xl font-black text-red-600">{openCount}</div>
            </CardContent>
          </Card>

          <Card className="glass border border-amber-100 bg-amber-50/30">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-1.5 mb-1">
                <Eye className="h-3.5 w-3.5 text-amber-500" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Reviewed</span>
              </div>
              <div className="text-3xl font-black text-amber-600">{reviewedCount}</div>
            </CardContent>
          </Card>

          <Card className="glass border border-emerald-100 bg-emerald-50/30">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-1.5 mb-1">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Resolved</span>
              </div>
              <div className="text-3xl font-black text-emerald-600">{resolvedCount}</div>
            </CardContent>
          </Card>

          <Card className="glass border border-red-100 bg-red-50/30">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center gap-1.5 mb-1">
                <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Critical</span>
              </div>
              <div className="text-3xl font-black text-red-600">{criticalCount}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Reports List */}
      <div className="space-y-3">
        {generating ? (
          <Card className="glass border border-white/20">
            <CardContent className="py-16 flex flex-col items-center justify-center gap-4">
              <div className="relative">
                <ShieldAlert className="h-14 w-14 text-amber-400 animate-pulse" />
                <Loader2 className="h-6 w-6 text-amber-600 animate-spin absolute -bottom-1 -right-1" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-foreground">Generating Mismatch Reports</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Analyzing alignment results → Detecting mismatches → Generating AI fixes...
                </p>
              </div>
            </CardContent>
          </Card>
        ) : reports.length === 0 ? (
          <Card className="glass border border-white/20">
            <CardContent className="py-16 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <FileWarning className="h-14 w-14 text-muted-foreground/20" />
              <div className="text-center">
                <p className="font-semibold">No mismatch reports found</p>
                <p className="text-sm mt-1">
                  To generate mismatch reports:
                  <br />✓ Select a project with alignment results
                  <br />✓ Click <strong>Generate Reports</strong> above
                  <br />✓ The AI will analyze drifts and produce actionable reports
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-2">
                <Search className="h-3.5 w-3.5" />
                {reports.length} Mismatch Report{reports.length !== 1 ? "s" : ""}
              </h2>
              <span className="text-xs text-muted-foreground">
                Sorted by severity • Click to expand details
              </span>
            </div>
            {reports.map((report) => (
              <MismatchRow
                key={report.id}
                report={report}
                onResolve={(m) => setResolving(m)}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}
