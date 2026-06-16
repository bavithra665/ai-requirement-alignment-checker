"use client";
/* eslint-disable react-hooks/exhaustive-deps */

import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api-client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertCircle, CheckCircle2, RefreshCw, Loader2, ExternalLink, ShieldAlert } from "lucide-react";

interface JiraStory {
  id: string;
  jira_issue_key: string;
  title: string;
  description?: string;
  status: string;
  story_type?: string;
  assignee?: string;
  priority?: string;
  external_url?: string;
  labels?: string[];
}

interface JiraStatus {
  configured: boolean;
  connected?: boolean;
  server_title?: string;
  base_url?: string;
  message?: string;
  setup_instructions?: string[];
  error?: string;
}

export default function JiraIntegrationPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [jiraStatus, setJiraStatus] = useState<JiraStatus | null>(null);
  const [stories, setStories] = useState<JiraStory[]>([]);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [loadingStories, setLoadingStories] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

   
  useEffect(() => {
    async function init() {
      try {
        setLoadingStatus(true);
        const [projList, status] = await Promise.all([
          api.getProjects(),
          api.getJiraStatus(),
        ]);
        setProjects(projList);
        setJiraStatus(status);

        if (projList.length > 0) {
          // Find first project with a Jira key
          const firstJiraProj = projList.find(p => p.jira_project_key);
          if (firstJiraProj) {
            setSelectedProjectId(firstJiraProj.id);
          } else {
            setSelectedProjectId(projList[0].id);
          }
        }
      } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
        console.error(errMsg);
        setError("Failed to load initial data. Ensure the backend server is running.");
      } finally {
        setLoadingStatus(false);
      }
    }
    init();
  }, []);

   
   
   
  useEffect(() => {
    if (selectedProjectId) {
      loadStories();
    } else {
      setStories([]);
    }
  }, [selectedProjectId]);

  const loadStories = async () => {
    try {
      setLoadingStories(true);
      setError(null);
      const data = await api.getJiraStories(selectedProjectId);
      setStories(data);
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      setStories([]);
      // Project might not have stories yet
      console.warn("Failed to load stories: ", errMsg);
    } finally {
      setLoadingStories(false);
    }
  };

  const handleSync = async () => {
    if (!selectedProjectId) return;
    try {
      setSyncing(true);
      setError(null);
      const res = await api.syncJiraStories(selectedProjectId);
      alert(res.message || `Successfully synced ${res.synced} stories!`);
      await loadStories();
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      setError(errMsg || "Sync failed. Check connection configuration.");
    } finally {
      setSyncing(false);
    }
  };

  const currentProject = projects.find((p) => p.id === selectedProjectId);

  if (loadingStatus) {
    return (
      <div className="flex flex-col items-center justify-center p-24">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground text-sm">Checking Jira integration state...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
          Jira Synchronization Desk
        </h1>
        <p className="text-muted-foreground text-sm">
          Map requirements to Jira stories, epics, and tasks to monitor implementation drift.
        </p>
      </div>

      {/* Jira Status Alert */}
      {jiraStatus && (
        <Card className={`glass border ${jiraStatus.configured ? 'border-emerald-500/20 bg-emerald-50/10' : 'border-amber-500/20 bg-amber-50/10'}`}>
          <CardHeader className="pb-3 flex flex-row items-center justify-between gap-4">
            <div className="space-y-1">
              <CardTitle className="text-lg flex items-center gap-2">
                {jiraStatus.configured ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-amber-500" />
                )}
                Jira Client Status: {jiraStatus.configured ? "Configured" : "Not Configured"}
              </CardTitle>
              <CardDescription>
                {jiraStatus.configured
                  ? `Connected to Jira Server: ${jiraStatus.server_title || "Atlassian Cloud"}`
                  : "Syncing requires Atlassian API tokens configured in the system backend env."}
              </CardDescription>
            </div>
            {jiraStatus.configured && (
              <Badge className="bg-emerald-100 text-emerald-800">Ready</Badge>
            )}
          </CardHeader>
          <CardContent className="text-sm">
            {jiraStatus.configured ? (
              <div className="space-y-1">
                <p>
                  <strong>API Endpoint:</strong>{" "}
                  <a
                    href={jiraStatus.base_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:underline inline-flex items-center gap-1 font-mono"
                  >
                    {jiraStatus.base_url} <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </p>
                {jiraStatus.error && (
                  <p className="text-red-500 font-semibold mt-2">
                    Connection Error: {jiraStatus.error}
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-3 mt-1">
                <div className="p-3 bg-white rounded border text-muted-foreground text-xs leading-relaxed font-mono">
                  {jiraStatus.setup_instructions?.map((inst, i) => (
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
        {/* Project & Settings Mapping */}
        <Card className="glass md:col-span-1 border border-white/20">
          <CardHeader>
            <CardTitle className="text-lg">Project Mapping</CardTitle>
            <CardDescription>Select alignment scope to sync Jira Stories.</CardDescription>
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
                <p>
                  <strong>Jira Project Key:</strong>{" "}
                  {currentProject.jira_project_key ? (
                    <span className="font-mono bg-white px-1.5 py-0.5 rounded border">
                      {currentProject.jira_project_key}
                    </span>
                  ) : (
                    <span className="text-red-500 italic">None Configured</span>
                  )}
                </p>
                <p>
                  <strong>Client Name:</strong> {currentProject.client_name || "Internal"}
                </p>
                <p>
                  <strong>Current Status:</strong> {currentProject.status}
                </p>
              </div>
            )}

            <Button
              className="w-full bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 text-white font-medium flex items-center justify-center gap-2"
              onClick={handleSync}
              disabled={
                syncing ||
                !jiraStatus?.configured ||
                !currentProject?.jira_project_key
              }
            >
              {syncing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Syncing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" /> Synchronize Stories
                </>
              )}
            </Button>
            
            {!currentProject?.jira_project_key && selectedProjectId && (
              <p className="text-[11px] text-amber-600 italic">
                Jira sync is disabled because this project doesn&apos;t have a Jira Project Key configured.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Stories Listing */}
        <Card className="glass md:col-span-2 border border-white/20">
          <CardHeader>
            <CardTitle className="text-lg">Synchronized Jira Issues</CardTitle>
            <CardDescription>
              Stories and Epics parsed from Jira project scope.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingStories ? (
              <div className="flex flex-col items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
                <span className="text-xs text-muted-foreground">Loading sync history...</span>
              </div>
            ) : stories.length === 0 ? (
              <div className="text-center p-12 text-muted-foreground">
                <RefreshCw className="h-12 w-12 mx-auto text-muted-foreground/30 mb-3" />
                <p className="text-sm">No synchronized issues found.</p>
                <p className="text-xs mt-1">Select a project and click Synchronize Stories.</p>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden bg-white max-h-[400px] overflow-y-auto">
                <Table>
                  <TableHeader className="bg-muted/30">
                    <TableRow>
                      <TableHead className="w-[120px]">Key</TableHead>
                      <TableHead>Title</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Assignee</TableHead>
                      <TableHead>Priority</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stories.map((story) => (
                      <TableRow key={story.id}>
                        <TableCell className="font-mono text-xs">
                          {story.external_url ? (
                            <a
                              href={story.external_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-primary hover:underline flex items-center gap-1 font-semibold"
                            >
                              {story.jira_issue_key} <ExternalLink className="h-3 w-3" />
                            </a>
                          ) : (
                            story.jira_issue_key
                          )}
                        </TableCell>
                        <TableCell className="font-medium text-xs max-w-[200px] truncate">
                          {story.title}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-[10px] py-0">
                            {story.story_type || "Story"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className="bg-blue-50 text-blue-800 text-[10px] border-blue-100">
                            {story.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {story.assignee || "Unassigned"}
                        </TableCell>
                        <TableCell className="text-xs">
                          {story.priority || "Medium"}
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
