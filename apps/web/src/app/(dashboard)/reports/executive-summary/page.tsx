"use client";
/* eslint-disable react-hooks/exhaustive-deps */

import { useEffect, useState } from "react";
import { api, Project, ExecutiveReport } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, FileBarChart, Download, Printer, ShieldAlert, Activity, Briefcase, Zap, Target } from "lucide-react";

export default function ExecutiveSummaryPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [report, setReport] = useState<ExecutiveReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

   
  useEffect(() => {
    async function init() {
      try {
        const projList = await api.getProjects();
        setProjects(projList);
        if (projList.length > 0) {
          setSelectedProjectId(projList[0].id);
        }
      } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
        setError("Failed to load projects.");
        console.warn(errMsg);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

   
  useEffect(() => {
    if (selectedProjectId) {
      loadReport();
    } else {
      setReport(null);
    }
  }, [selectedProjectId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getExecutiveReport(selectedProjectId);
      setReport(data);
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      setReport(null);
      console.warn("Failed to load executive report:", errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedProjectId) return;
    try {
      setGenerating(true);
      setError(null);
      const data = await api.getExecutiveReport(selectedProjectId);
      setReport(data);
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      setError(errMsg || "Failed to generate report.");
    } finally {
      setGenerating(false);
    }
  };

  const handleExportPdf = async () => {
    if (!selectedProjectId || !report) return;
    try {
      setGenerating(true);
      setError(null);
      // @ts-expect-error - no types for jspdf-html2canvas
      const html2PDF = (await import("jspdf-html2canvas")).default;
      const element = document.getElementById("report-content");
      if (!element) return;

      await html2PDF(element, {
        jsPDF: {
          unit: "mm",
          format: "a4",
          orientation: "portrait"
        },
        imageType: "image/jpeg",
        output: `executive_report_${selectedProjectId}.pdf`
      });
    } catch (error: unknown) {
      const errMsg = error instanceof Error ? error.message : String(error);
      setError(errMsg || "Failed to export PDF.");
    } finally {
      setGenerating(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const healthColor = (status: string) => {
    switch(status) {
      case "Excellent": return "text-emerald-600 bg-emerald-50 border-emerald-200";
      case "Good": return "text-green-600 bg-green-50 border-green-200";
      case "Needs Attention": return "text-amber-600 bg-amber-50 border-amber-200";
      case "Critical": return "text-red-600 bg-red-50 border-red-200";
      default: return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const severityColor = (sev: string) => {
    switch(sev) {
      case "Critical": return "bg-red-100 text-red-800 border-red-200";
      case "High": return "bg-orange-100 text-orange-800 border-orange-200";
      case "Medium": return "bg-amber-100 text-amber-800 border-amber-200";
      case "Low": return "bg-green-100 text-green-800 border-green-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header (No print) */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 print:hidden">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <FileBarChart className="h-6 w-6 text-[#0096C7]" />
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Executive Report
            </h1>
          </div>
          <p className="text-muted-foreground text-sm">
            High-level management summary of project alignment and risks.
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
            onClick={handleGenerate}
            disabled={generating || !selectedProjectId}
            className="bg-gradient-to-r from-[#0096C7] to-[#0077b6] hover:from-[#0077b6] hover:to-[#023e8a] text-white font-semibold shadow-md flex items-center gap-2"
          >
            {generating ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Generating...</>
            ) : (
              "Generate Report"
            )}
          </Button>
          
          <Button
            variant="outline"
            onClick={handleExportPdf}
            disabled={!report}
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4" /> PDF
          </Button>

          <Button
            variant="outline"
            onClick={handlePrint}
            disabled={!report}
            className="flex items-center gap-2"
          >
            <Printer className="h-4 w-4" /> Print
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-3 print:hidden">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {loading ? (
        <div className="p-24 flex flex-col items-center justify-center print:hidden">
          <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">Loading executive report...</p>
        </div>
      ) : !report ? (
        <Card className="glass border border-white/20 print:hidden">
          <CardContent className="py-16 flex flex-col items-center justify-center gap-3 text-muted-foreground">
            <FileBarChart className="h-14 w-14 text-muted-foreground/30 mb-2" />
            <div className="text-center">
              <p className="font-semibold text-foreground">No executive report available</p>
              <p className="text-sm mt-1">
                Select a project and click Generate Report.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div id="report-content" className="space-y-8 bg-white p-2 md:p-8 rounded-xl print:p-0 print:bg-transparent">
          
          {/* Report Header */}
          <div className="border-b pb-6">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-black text-slate-900 tracking-tight mb-2">
                  Project Alignment Summary
                </h1>
                <h2 className="text-xl text-slate-500 font-medium">{report.project_summary.name}</h2>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-1">Generated</div>
                <div className="text-slate-700 font-medium">{new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-4 mt-6">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-100 border border-slate-200 text-sm font-medium text-slate-700">
                <Briefcase className="h-4 w-4 text-slate-400" />
                Client: {report.project_summary.client_name || "Internal"}
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-100 border border-slate-200 text-sm font-medium text-slate-700">
                <Activity className="h-4 w-4 text-slate-400" />
                Status: {report.project_summary.status}
              </div>
            </div>
          </div>

          {/* KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-5 rounded-xl border ${healthColor(report.health.health_status)}`}>
              <div className="text-xs font-bold uppercase tracking-wider mb-1 opacity-70">Overall Health</div>
              <div className="text-4xl font-black mb-1">{report.health.health_score}</div>
              <div className="text-sm font-semibold">{report.health.health_status}</div>
            </div>
            
            <div className="p-5 rounded-xl border bg-slate-50 border-slate-200">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Avg Alignment</div>
              <div className="text-4xl font-black text-slate-800 mb-1">{report.alignment_overview.avg_score}%</div>
              <div className="text-sm font-medium text-slate-500">Traceability Match</div>
            </div>

            <div className="p-5 rounded-xl border bg-red-50 border-red-200">
              <div className="text-xs font-bold uppercase tracking-wider text-red-600/70 mb-1">Open Risks</div>
              <div className="text-4xl font-black text-red-700 mb-1">{report.health.open_mismatches}</div>
              <div className="text-sm font-medium text-red-600">Unresolved Gaps</div>
            </div>

            <div className="p-5 rounded-xl border bg-emerald-50 border-emerald-200">
              <div className="text-xs font-bold uppercase tracking-wider text-emerald-600/70 mb-1">Aligned Req.</div>
              <div className="text-4xl font-black text-emerald-700 mb-1">{report.alignment_overview.aligned}</div>
              <div className="text-sm font-medium text-emerald-600">Out of {report.alignment_overview.total} Total</div>
            </div>
          </div>

          {/* Executive Narrative */}
          <div>
            <h3 className="text-lg font-bold text-slate-900 border-b pb-2 mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-indigo-500" />
              AI Executive Summary
            </h3>
            <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed bg-indigo-50/50 p-6 rounded-xl border border-indigo-100">
              {(report.narrative || '').split('\n\n').map((paragraph, idx) => (
                <p key={idx} className={idx > 0 ? "mt-4" : ""}>{paragraph}</p>
              ))}
            </div>
          </div>

          {/* Key Recommendations */}
          <div className="page-break-before">
            <h3 className="text-lg font-bold text-slate-900 border-b pb-2 mb-4 flex items-center gap-2">
              <Target className="h-5 w-5 text-amber-500" />
              Key Recommendations
            </h3>
            <div className="bg-amber-50/50 p-6 rounded-xl border border-amber-100">
              <ul className="space-y-3">
                {(Array.isArray(report.recommendations)
                  ? report.recommendations
                  : typeof report.recommendations === 'string'
                  ? report.recommendations.split('\n')
                  : []
                )
                  .filter(line => line && typeof line === 'string' && line.trim().length > 0)
                  .map((rec, idx) => (
                    <li key={idx} className="flex gap-3 text-slate-700">
                      <span className="text-amber-500 font-bold mt-0.5">•</span>
                      <span>{rec.replace(/^[-\*\d\.\s]+/, '')}</span>
                    </li>
                  ))}
              </ul>
            </div>
          </div>

          {/* Top Risks */}
          {report.top_risks.length > 0 && (
            <div>
              <h3 className="text-lg font-bold text-slate-900 border-b pb-2 mb-4 flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-red-500" />
                Top Implementation Risks
              </h3>
              <div className="border rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 border-b text-slate-500 font-semibold uppercase text-xs tracking-wider">
                    <tr>
                      <th className="p-4">Severity</th>
                      <th className="p-4">Risk Type</th>
                      <th className="p-4">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {report.top_risks.map((risk, idx) => (
                      <tr key={idx} className="bg-white">
                        <td className="p-4 whitespace-nowrap">
                          <Badge className={`${severityColor(risk.severity)} border text-xs`}>{risk.severity}</Badge>
                        </td>
                        <td className="p-4 font-medium text-slate-900">{risk.mismatch_type}</td>
                        <td className="p-4 text-slate-600">{risk.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      )}
      
      {/* Print styles */}
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
          body { background: white !important; }
          .page-break-before { page-break-before: always; }
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        }
      `}} />
    </div>
  );
}
