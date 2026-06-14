"use client";

import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api-client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertCircle, CheckCircle2, RefreshCw, Loader2, ExternalLink, ShieldAlert, Code, Check } from "lucide-react";

interface PullRequest {
  id: string;
  pr_number: number;
  repository_url: string;
  title: string;
  pr_description?: string;
  status: string;
  author?: string;
  branch?: string;
  base_branch?: string;
  head_sha?: string;
  merged_at?: string;
  changed_files?: string[];
}

interface GitHubStatus {
  configured: boolean;
  connected?: boolean;
  github_user?: string;
  rate_limit_remaining?: number;
  message?: string;
  setup_instructions?: string[];
  error?: string;
}

export default function GitHubIntegrationPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [ghStatus, setGhStatus] = useState<GitHubStatus | null>(null);
  const [prs, setPrs] = useState<PullRequest[]>([]);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [loadingPrs, setLoadingPrs] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [extractingId, setExtractingId] = useState<string | null>(null);
  const [extractedSuccess, setExtractedSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        setLoadingStatus(true);
        const [projList, status] = await Promise.all([
          api.getProjects(),
          api.getGitHubStatus(),
        ]);
        setProjects(projList);
        setGhStatus(status);

        if (projList.length > 0) {
          // Find first project with a repository URL
          const firstRepoProj = projList.find(p => p.repository_url);
          if (firstRepoProj) {
            setSelectedProjectId(firstRepoProj.id);
          } else {
            setSelectedProjectId(projList[0].id);
          }
        }
      } catch (err: any) {
        console.error(err);
        setError("Failed to load initial data. Ensure the backend server is running.");
      } finally {
        setLoadingStatus(false);
      }
    }
    init();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadPrs();
    } else {
      setPrs([]);
    }
  }, [selectedProjectId]);

  const loadPrs = async () => {
    try {
      setLoadingPrs(true);
      setError(null);
      const data = await api.getPullRequests(selectedProjectId);
      setPrs(data);
    } catch (err: any) {
      setPrs([]);
      console.warn("Failed to load PRs: ", err);
    } finally {
      setLoadingPrs(false);
    }
  };

  const handleSync = async () => {
    if (!selectedProjectId) return;
    try {
      setSyncing(true);
      setError(null);
      const res = await api.syncPullRequests(selectedProjectId);
      alert(res.message || `Successfully synced ${res.synced} pull requests!`);
      await loadPrs();
    } catch (err: any) {
      setError(err.message || "Sync failed. Check repository URL and connection token.");
    } finally {
      setSyncing(false);
    }
  };

  const handleExtract = async (prId: string) => {
    try {
      setExtractingId(prId);
      setError(null);
      const res = await api.extractSymbols(prId);
      setExtractedSuccess(prId);
      setTimeout(() => setExtractedSuccess(null), 3000);
      alert(
        `Extraction Completed!\nProcessed Files: ${res.processed_files}\nFunctions: ${res.total_functions}\nClasses: ${res.total_classes}\nEndpoints: ${res.total_endpoints}`
      );
    } catch (err: any) {
      setError(err.message || "Symbol extraction failed.");
    } finally {
      setExtractingId(null);
    }
  };

  const currentProject = projects.find((p) => p.id === selectedProjectId);

  if (loadingStatus) {
    return (
      <div className="flex flex-col items-center justify-center p-24">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground text-sm">Checking GitHub integration state...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
          GitHub Pull Request synchronization
        </h1>
        <p className="text-muted-foreground text-sm">
          Monitor source pull requests and extract code signatures (functions, classes, endpoints).
        </p>
      </div>

      {/* GitHub Status Alert */}
      {ghStatus && (
        <Card className={`glass border ${ghStatus.configured ? 'border-emerald-500/20 bg-emerald-50/10' : 'border-amber-500/20 bg-amber-50/10'}`}>
          <CardHeader className="pb-3 flex flex-row items-center justify-between gap-4">
            <div className="space-y-1">
              <CardTitle className="text-lg flex items-center gap-2">
                {ghStatus.configured ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-amber-500" />
                )}
                GitHub Connection: {ghStatus.configured ? "Configured" : "Not Configured"}
              </CardTitle>
              <CardDescription>
                {ghStatus.configured
                  ? `Authorized as user: ${ghStatus.github_user || "Token User"}`
                  : "Token integration requires GITHUB_TOKEN configured in the backend env."}
              </CardDescription>
            </div>
            {ghStatus.configured && (
              <Badge className="bg-emerald-100 text-emerald-800">Ready</Badge>
            )}
          </CardHeader>
          <CardContent className="text-sm">
            {ghStatus.configured ? (
              <div className="space-y-1">
                <p>
                  <strong>API Health:</strong> GitHub connection active.
                </p>
                {ghStatus.rate_limit_remaining !== undefined && (
                  <p className="text-xs text-muted-foreground">
                    Rate Limit Remaining: {ghStatus.rate_limit_remaining} requests
                  </p>
                )}
                {ghStatus.error && (
                  <p className="text-red-500 font-semibold mt-2">
                    Connection Error: {ghStatus.error}
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-3 mt-1">
                <div className="p-3 bg-white rounded border text-muted-foreground text-xs leading-relaxed font-mono">
                  {ghStatus.setup_instructions?.map((inst, i) => (
                    <div key={i}>{inst}</div>
                  ))}
                </div>
                <p className="text-xs text-amber-700/80">
                  Please update your local <code className="bg-amber-100/50 px-1 py-0.5 rounded font-mono font-bold">.env</code> file.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {/* Control Panel */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Project Selection & Sync Panel */}
        <Card className="glass md:col-span-1 border border-white/20">
          <CardHeader>
            <CardTitle className="text-lg">Project Scope</CardTitle>
            <CardDescription>Target repository to pull updates.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Select Project</label>
              <select
                className="w-full bg-white border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
              >
                <option value="">-- Select Project --</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {currentProject && (
              <div className="p-3.5 bg-muted/10 border rounded-lg space-y-2 text-xs">
                <p className="break-all">
                  <strong>Repo URL:</strong>{" "}
                  {currentProject.repository_url ? (
                    <a
                      href={currentProject.repository_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary hover:underline font-mono inline-flex items-center gap-0.5"
                    >
                      {currentProject.repository_url} <ExternalLink className="h-3 w-3 inline" />
                    </a>
                  ) : (
                    <span className="text-red-500 italic">None Configured</span>
                  )}
                </p>
                <p>
                  <strong>Client Name:</strong> {currentProject.client_name || "Internal"}
                </p>
                <p>
                  <strong>Status:</strong> {currentProject.status}
                </p>
              </div>
            )}

            <Button
              className="w-full bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white font-medium flex items-center justify-center gap-2"
              onClick={handleSync}
              disabled={
                syncing ||
                !ghStatus?.configured ||
                !currentProject?.repository_url
              }
            >
              {syncing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Syncing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" /> Fetch Pull Requests
                </>
              )}
            </Button>

            {!currentProject?.repository_url && selectedProjectId && (
              <p className="text-[11px] text-amber-600 italic">
                PR Sync is disabled because this project doesn't have a Repository URL configured.
              </p>
            )}
          </CardContent>
        </Card>

        {/* PR History & Extraction Panel */}
        <Card className="glass md:col-span-2 border border-white/20">
          <CardHeader>
            <CardTitle className="text-lg">Pull Request Dashboard</CardTitle>
            <CardDescription>
              Recent PR synchronization data and code extraction triggers.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingPrs ? (
              <div className="flex flex-col items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
                <span className="text-xs text-muted-foreground">Loading pull requests...</span>
              </div>
            ) : prs.length === 0 ? (
              <div className="text-center p-12 text-muted-foreground">
                <Code className="h-12 w-12 mx-auto text-muted-foreground/30 mb-3" />
                <p className="text-sm">No pull requests synced yet.</p>
                <p className="text-xs mt-1">Select a project and click Fetch Pull Requests.</p>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden bg-white max-h-[400px] overflow-y-auto">
                <Table>
                  <TableHeader className="bg-muted/30">
                    <TableRow>
                      <TableHead className="w-[80px]">PR #</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Branch</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Files</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {prs.map((pr) => (
                      <TableRow key={pr.id}>
                        <TableCell className="font-semibold text-xs text-muted-foreground">
                          #{pr.pr_number}
                        </TableCell>
                        <TableCell className="font-medium text-xs max-w-[180px] truncate" title={pr.title}>
                          {pr.title}
                        </TableCell>
                        <TableCell className="font-mono text-[11px] max-w-[120px] truncate" title={pr.branch}>
                          {pr.branch || "main"}
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            pr.status === "merged" ? "bg-purple-100 text-purple-800" :
                            pr.status === "closed" ? "bg-red-100 text-red-800" :
                            "bg-green-100 text-green-800"
                          }>
                            {pr.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground font-semibold">
                          {pr.changed_files?.length || 0}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant={extractedSuccess === pr.id ? "default" : "outline"}
                            className={extractedSuccess === pr.id ? "bg-emerald-600 hover:bg-emerald-700 text-white" : "text-xs font-semibold"}
                            onClick={() => handleExtract(pr.id)}
                            disabled={extractingId === pr.id || !ghStatus?.configured}
                          >
                            {extractingId === pr.id ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : extractedSuccess === pr.id ? (
                              <Check className="h-3.5 w-3.5" />
                            ) : (
                              <>
                                <Code className="h-3.5 w-3.5 mr-1" /> Extract Code
                              </>
                            )}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
