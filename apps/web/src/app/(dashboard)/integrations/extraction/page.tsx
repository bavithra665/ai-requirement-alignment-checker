"use client";

import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api-client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, Code, FileCode, Server, Terminal, ShieldAlert, Cpu } from "lucide-react";

interface PullRequest {
  id: string;
  pr_number: number;
  title: string;
}

interface CodeArtifact {
  id: string;
  pull_request_id: string;
  artifact_type: string;  // "Function", "Class", "API Endpoint"
  artifact_name: string;
  file_path: string;
  artifact_metadata?: {
    line_number?: number;
    args?: string[];
    is_async?: boolean;
    decorators?: string[];
    base_classes?: string[];
    http_method?: string;
    function_name?: string;
  };
}

export default function CodeExtractionPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [prs, setPrs] = useState<PullRequest[]>([]);
  const [selectedPrId, setSelectedPrId] = useState<string>("");
  
  const [symbols, setSymbols] = useState<CodeArtifact[]>([]);
  const [typeFilter, setTypeFilter] = useState<string>(""); // empty = All
  
  const [loadingPrs, setLoadingPrs] = useState(false);
  const [loadingSymbols, setLoadingSymbols] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load Projects on mount
  useEffect(() => {
    async function loadProjects() {
      try {
        const projList = await api.getProjects();
        setProjects(projList);
        if (projList.length > 0) {
          setSelectedProjectId(projList[0].id);
        }
      } catch (err: any) {
        console.error(err);
        setError("Failed to load projects. Make sure api is running.");
      }
    }
    loadProjects();
  }, []);

  // Load PRs when project changes
  useEffect(() => {
    if (selectedProjectId) {
      loadProjectPrs();
    } else {
      setPrs([]);
      setSelectedPrId("");
    }
  }, [selectedProjectId]);

  // Load Symbols when PR or filter changes
  useEffect(() => {
    if (selectedPrId) {
      loadSymbols();
    } else {
      setSymbols([]);
    }
  }, [selectedPrId, typeFilter]);

  const loadProjectPrs = async () => {
    try {
      setLoadingPrs(true);
      const data = await api.getPullRequests(selectedProjectId);
      setPrs(data);
      if (data.length > 0) {
        setSelectedPrId(data[0].id);
      } else {
        setSelectedPrId("");
      }
    } catch (err) {
      console.error(err);
      setPrs([]);
      setSelectedPrId("");
    } finally {
      setLoadingPrs(false);
    }
  };

  const loadSymbols = async () => {
    try {
      setLoadingSymbols(true);
      setError(null);
      const data = await api.getSymbols(selectedPrId, typeFilter || undefined);
      setSymbols(data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch extracted symbols.");
    } finally {
      setLoadingSymbols(false);
    }
  };

  const handleExtract = async () => {
    if (!selectedPrId) return;
    try {
      setExtracting(true);
      setError(null);
      await api.extractSymbols(selectedPrId);
      await loadSymbols();
    } catch (err: any) {
      setError(err.message || "Failed to trigger symbol extraction.");
    } finally {
      setExtracting(false);
    }
  };

  const getArtifactIcon = (type: string) => {
    switch (type) {
      case "API Endpoint":
        return <Server className="h-4 w-4 text-emerald-500" />;
      case "Class":
        return <Cpu className="h-4 w-4 text-indigo-500" />;
      case "Function":
      default:
        return <Terminal className="h-4 w-4 text-sky-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
          Code Signature Extraction
        </h1>
        <p className="text-muted-foreground text-sm">
          Browse AST-extracted functions, classes, and endpoints found in repository changes.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          <div>{error}</div>
        </div>
      )}

      {/* Control Selector Panel */}
      <Card className="glass border border-white/20">
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            {/* Project Select */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Project Scope</label>
              <select
                className="w-full bg-white border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
              >
                <option value="">Select Project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* PR Select */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Pull Request</label>
              {loadingPrs ? (
                <div className="flex items-center h-10 px-3 text-xs text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> Loading PRs...
                </div>
              ) : (
                <select
                  className="w-full bg-white border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none"
                  value={selectedPrId}
                  onChange={(e) => setSelectedPrId(e.target.value)}
                  disabled={prs.length === 0}
                >
                  <option value="">-- Select Pull Request --</option>
                  {prs.map((pr) => (
                    <option key={pr.id} value={pr.id}>
                      PR #{pr.pr_number} - {pr.title}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Type Filter */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Artifact Type</label>
              <select
                className="w-full bg-white border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary outline-none"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                disabled={!selectedPrId}
              >
                <option value="">All Types</option>
                <option value="Function">Functions</option>
                <option value="Class">Classes</option>
                <option value="API Endpoint">API Endpoints</option>
              </select>
            </div>

            {/* Quick Extraction Trigger */}
            <div className="flex items-end">
              <Button
                className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium flex items-center justify-center gap-2"
                onClick={handleExtract}
                disabled={extracting || !selectedPrId}
              >
                {extracting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Analyzing...
                  </>
                ) : (
                  <>
                    <Code className="h-4 w-4" /> Run Code Analyzer
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Extracted Symbols Grid/Table */}
      <Card className="glass border border-white/20">
        <CardHeader>
          <CardTitle className="text-lg">Extracted Normalized Artifacts</CardTitle>
          <CardDescription>
            Normalized schema structures generated for alignment vector indexing.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingSymbols ? (
            <div className="flex flex-col items-center justify-center p-16">
              <Loader2 className="h-10 w-10 animate-spin text-primary mb-2" />
              <span className="text-sm text-muted-foreground">Parsing AST symbols...</span>
            </div>
          ) : symbols.length === 0 ? (
            <div className="text-center p-16 text-muted-foreground">
              <FileCode className="h-16 w-16 mx-auto text-muted-foreground/30 mb-3" />
              <p className="text-sm font-semibold">No extracted artifacts found for this PR.</p>
              <p className="text-xs mt-1">Make sure you run the Code Analyzer tool above.</p>
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden bg-white max-h-[500px] overflow-y-auto">
              <Table>
                <TableHeader className="bg-muted/30">
                  <TableRow>
                    <TableHead className="w-[180px]">Artifact Name</TableHead>
                    <TableHead className="w-[120px]">Type</TableHead>
                    <TableHead>File Path</TableHead>
                    <TableHead className="w-[80px]">Line</TableHead>
                    <TableHead>Signature / Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {symbols.map((sym) => (
                    <TableRow key={sym.id} className="hover:bg-muted/10">
                      <TableCell className="font-mono text-xs font-semibold text-foreground break-all">
                        {sym.artifact_name}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="flex items-center gap-1.5 w-fit text-[10px] font-bold py-0.5">
                          {getArtifactIcon(sym.artifact_type)}
                          {sym.artifact_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono break-all" title={sym.file_path}>
                        {sym.file_path}
                      </TableCell>
                      <TableCell className="text-xs font-mono text-muted-foreground">
                        {sym.artifact_metadata?.line_number || "—"}
                      </TableCell>
                      <TableCell className="text-xs">
                        {sym.artifact_type === "API Endpoint" && (
                          <div className="flex items-center gap-2">
                            <Badge className="bg-emerald-100 text-emerald-800 text-[10px] font-bold border-emerald-200">
                              {sym.artifact_metadata?.http_method || "GET"}
                            </Badge>
                            <span className="font-mono text-[11px] text-muted-foreground">
                              handler: {sym.artifact_metadata?.function_name}()
                            </span>
                          </div>
                        )}
                        {sym.artifact_type === "Function" && (
                          <div className="space-y-1">
                            <span className="font-mono text-[11px] text-muted-foreground">
                              def {sym.artifact_name}(
                              {sym.artifact_metadata?.args?.join(", ") || ""}
                              )
                            </span>
                            {sym.artifact_metadata?.is_async && (
                              <Badge variant="secondary" className="text-[8px] scale-90 py-0 ml-1">
                                async
                              </Badge>
                            )}
                          </div>
                        )}
                        {sym.artifact_type === "Class" && (
                          <span className="font-mono text-[11px] text-muted-foreground">
                            class {sym.artifact_name}
                            {sym.artifact_metadata?.base_classes && sym.artifact_metadata.base_classes.length > 0
                              ? `(${sym.artifact_metadata.base_classes.join(", ")})`
                              : ""}
                          </span>
                        )}
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
  );
}
