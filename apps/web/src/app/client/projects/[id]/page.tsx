"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import {
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
  Loader2,
  FileText,
  Sparkles,
  MessageSquare,
  Lock,
} from "lucide-react";

interface RequirementVersion {
  id: string;
  requirement_id: string;
  requirement_title: string;
  version_number: number;
  content: string;
  ai_summary: string | null;
  status: string;
  is_baseline: boolean;
  created_at: string;
}

function statusBadge(status: string) {
  switch (status) {
    case "Approved":
      return (
        <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200 border text-[11px]">
          <CheckCircle className="h-3 w-3 mr-1" /> Approved
        </Badge>
      );
    case "Changes Requested":
      return (
        <Badge className="bg-amber-100 text-amber-700 border-amber-200 border text-[11px]">
          <XCircle className="h-3 w-3 mr-1" /> Changes Requested
        </Badge>
      );
    default:
      return (
        <Badge className="bg-sky-100 text-sky-700 border-sky-200 border text-[11px]">
          <Clock className="h-3 w-3 mr-1" /> Pending Review
        </Badge>
      );
  }
}

export default function ClientProjectPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [versions, setVersions] = useState<RequirementVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedVersion, setSelectedVersion] = useState<RequirementVersion | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [comment, setComment] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    loadVersions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const loadVersions = async () => {
    try {
      setIsLoading(true);
      const data: RequirementVersion[] = await api.client.getRequirementVersions(projectId);
      // Sort by requirement_title ascending
      const sorted = [...data].sort((a, b) =>
        (a.requirement_title || "").localeCompare(b.requirement_title || "")
      );
      setVersions(sorted);
      if (sorted.length > 0) setSelectedVersion(sorted[0]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load requirements");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedVersion) return;
    setIsSubmitting(true);
    setError("");
    try {
      await api.client.approveRequirementVersion(projectId, selectedVersion.id, comment);
      setComment("");
      setSuccessMsg(`"${selectedVersion.requirement_title}" has been approved!`);
      setTimeout(() => setSuccessMsg(""), 4000);
      await loadVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!selectedVersion) return;

    setIsSubmitting(true);
    setError("");
    try {
      await api.client.rejectRequirementVersion(projectId, selectedVersion.id, comment);
      setComment("");
      setSuccessMsg(`Changes requested for "${selectedVersion.requirement_title}".`);
      setTimeout(() => setSuccessMsg(""), 4000);
      await loadVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to request changes");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-1">Requirement Review</h1>
        <p className="text-muted-foreground text-sm">
          Review each requirement and provide your approval or request changes.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Success */}
      {successMsg && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm">
          <CheckCircle className="h-4 w-4 shrink-0" />
          {successMsg}
        </div>
      )}

      {versions.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-20 text-muted-foreground">
          <FileText className="h-12 w-12 mb-3 text-muted-foreground/30" />
          <p className="text-sm">No requirements available for review yet.</p>
        </div>
      ) : (
        <div className="grid lg:grid-cols-2 gap-0 border rounded-2xl overflow-hidden shadow-sm min-h-[600px]">
          {/* ── LEFT PANEL: Full Requirements List ── */}
          <div className="border-r bg-white overflow-y-auto max-h-[80vh]">
            <div className="sticky top-0 bg-white border-b px-5 py-4 z-10">
              <h2 className="font-semibold text-base text-foreground flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                All Requirements
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                {versions.length} requirement{versions.length !== 1 ? "s" : ""} · Click to review
              </p>
            </div>

            <div className="divide-y">
              {versions.map((v, idx) => {
                const isSelected = selectedVersion?.id === v.id;
                return (
                  <button
                    key={v.id}
                    onClick={() => { setSelectedVersion(v); setComment(""); }}
                    className={`w-full text-left px-5 py-4 transition-all hover:bg-muted/30 ${
                      isSelected ? "bg-primary/5 border-l-4 border-l-primary" : "border-l-4 border-l-transparent"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 min-w-0">
                        {/* Index number */}
                        <span className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 ${
                          isSelected ? "bg-primary text-white" : "bg-muted text-muted-foreground"
                        }`}>
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <div className="min-w-0">
                          <p className={`text-sm font-semibold break-words leading-snug ${
                            isSelected ? "text-primary" : "text-foreground"
                          }`}>
                            {v.requirement_title || v.content.slice(0, 80)}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            v{v.version_number}.0 · {new Date(v.created_at).toLocaleDateString("en-GB")}
                          </p>
                        </div>
                      </div>
                      <div className="shrink-0">{statusBadge(v.status)}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── RIGHT PANEL: Detail + Action ── */}
          <div className="bg-slate-50/60 overflow-y-auto max-h-[80vh]">
            {selectedVersion ? (
              <div className="space-y-0">
                {/* Requirement title header */}
                <div className="bg-white border-b px-6 py-5">
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div>
                      <h3 className="text-lg font-bold text-foreground leading-snug break-words">
                        {selectedVersion.requirement_title}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        Version {selectedVersion.version_number}.0
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      {statusBadge(selectedVersion.status)}
                      {selectedVersion.is_baseline && (
                        <Badge className="bg-primary/10 text-primary border-primary/20 border text-[11px]">
                          <Lock className="h-3 w-3 mr-1" /> Baseline
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                {/* AI Executive Summary */}
                {selectedVersion.ai_summary && (
                  <div className="px-6 py-5 border-b bg-white">
                    <h4 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-3">
                      <Sparkles className="h-4 w-4 text-purple-500" />
                      AI Executive Summary
                    </h4>
                    <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                      {selectedVersion.ai_summary}
                    </p>
                  </div>
                )}

                {/* Full Requirement Content */}
                <div className="px-6 py-5 border-b bg-white">
                  <h4 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-3">
                    <FileText className="h-4 w-4 text-blue-500" />
                    Requirement Details
                  </h4>
                  <div className="p-4 bg-muted/30 rounded-xl border text-sm text-foreground whitespace-pre-wrap leading-relaxed font-mono">
                    {selectedVersion.content}
                  </div>
                </div>

                {/* Action Section */}
                {selectedVersion.status === "Approved" ? (
                  <div className="px-6 py-5 bg-white">
                    <div className="flex items-start gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                      <CheckCircle className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="font-semibold text-emerald-800 text-sm">Already Approved</p>
                        <p className="text-xs text-emerald-700 mt-0.5">
                          This requirement has been approved and locked as a production baseline. If you need changes, request them below.
                        </p>

                        <div className="mt-4 space-y-4">
                          <div>
                            <label htmlFor="comment" className="block text-xs font-semibold text-muted-foreground mb-1.5">
                              Comment (Required for request)
                            </label>
                            <textarea
                              id="comment"
                              placeholder="Explain what changes you need..."
                              value={comment}
                              onChange={(e) => setComment(e.target.value)}
                              rows={3}
                              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none resize-none transition-all"
                            />
                          </div>

                          <div className="flex gap-3">
                            <Button
                              onClick={async () => {
                                await handleReject();
                              }}
                              disabled={isSubmitting}
                              variant="outline"
                              className="flex-1 border-amber-400 text-amber-700 hover:bg-amber-50 font-semibold rounded-xl h-10"
                            >
                              {isSubmitting ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                              ) : (
                                <XCircle className="h-4 w-4 mr-2" />
                              )}
                              Request Changes
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="px-6 py-5 bg-white">
                    <h4 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
                      <MessageSquare className="h-4 w-4 text-slate-500" />
                      Your Action
                    </h4>

                    <div className="space-y-4">
                      <div>
                        <label htmlFor="comment" className="block text-xs font-semibold text-muted-foreground mb-1.5">
                          Comment (Optional)
                        </label>
                        <textarea
                          id="comment"
                          placeholder="Add a comment..."
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                          rows={3}
                          className="w-full px-3 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary/50 outline-none resize-none transition-all"
                        />
                      </div>

                      <div className="flex gap-3">
                        <Button
                          onClick={handleApprove}
                          disabled={isSubmitting}
                          className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl h-10"
                        >
                          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                          Approve
                        </Button>
                        <Button
                          onClick={handleReject}
                          disabled={isSubmitting}
                          variant="outline"
                          className="flex-1 border-amber-400 text-amber-700 hover:bg-amber-50 font-semibold rounded-xl h-10"
                        >
                          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <XCircle className="h-4 w-4 mr-2" />}
                          Request Changes
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-20 text-muted-foreground">
                <FileText className="h-12 w-12 mb-3 text-muted-foreground/30" />
                <p className="text-sm">Select a requirement to review</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
