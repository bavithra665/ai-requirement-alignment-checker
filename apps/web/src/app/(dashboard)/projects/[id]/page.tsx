"use client";
/* eslint-disable react-hooks/exhaustive-deps */

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ArrowLeft,
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  Sparkles,
  History,
  Loader2,
  Lock,
  GitCommit,
  UserCheck
} from "lucide-react";
import { api, Project, RequirementVersion } from "@/lib/api-client";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [versions, setVersions] = useState<RequirementVersion[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [comment, setComment] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const projData = await api.getProject(projectId);
      setProject(projData);

      // Fetch requirements versions
      const versionsData = await api.getRequirements(projectId);
      setVersions(versionsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

   
  useEffect(() => {
    if (projectId) {
      fetchData();
    }
  }, [projectId]);

  // Drag and Drop Handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    if (!file.name.endsWith(".pdf") && !file.name.endsWith(".docx")) {
      alert("Only PDF and DOCX files are supported!");
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(10);
      
      const interval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 15;
        });
      }, 300);

      const res = await api.uploadBRD(projectId, file) as Record<string, unknown>;
      clearInterval(interval);
      setUploadProgress(100);
      
      alert((res?.message as string) || "File uploaded successfully!");
      fetchData();
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      alert(errMsg || "Failed to upload file");
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleReview = async (versionId: string, action: "approve" | "request_changes") => {
    try {
      setActionLoading(versionId);
      await api.reviewRequirement(versionId, action, comment || undefined);
      setComment("");
      alert(`Successfully ${action === "approve" ? "approved" : "requested changes"}`);
      
      // Update Project Status if first approval
      if (action === "approve" && project?.status === "Draft") {
        await api.updateProject(projectId, { status: "In Progress" });
      }
      
      fetchData();
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      alert(errMsg || "Failed to process review");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-24">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground text-sm">Loading project analysis workspace...</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center p-24 text-center">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h3 className="text-xl font-bold">Project Not Found</h3>
        <Button onClick={() => router.push(user?.role === 'client' ? '/client/dashboard' : '/dashboard')} className="mt-4">
          Return to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(user?.role === 'client' ? '/client/dashboard' : '/dashboard')}
            className="rounded-full shrink-0"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
                {project.name}
              </h1>
              <Badge className={
                project.status === "Completed" ? "bg-green-100 text-green-800" :
                project.status === "In Progress" ? "bg-blue-100 text-blue-800" :
                "bg-amber-100 text-amber-800"
              }>
                {project.status}
              </Badge>
            </div>
            <p className="text-muted-foreground text-sm">
              Client: <span className="font-semibold text-foreground">{project.client_name || "Internal"}</span>
              {project.client_email && (
                <span className="ml-2 text-xs text-muted-foreground">({project.client_email})</span>
              )}
              {project.jira_project_key && (
                <>
                  <span className="mx-2">•</span>
                  Jira Key: <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-xs">{project.jira_project_key}</span>
                </>
              )}
            </p>
            {project.status_reason && (
              <div className="mt-3 p-3 bg-muted/40 border border-muted rounded-md max-w-2xl">
                <p className="text-sm text-muted-foreground">
                  <strong className="text-foreground">Status Reason:</strong> {project.status_reason}
                </p>
              </div>
            )}
          </div>
        </div>

        {project.repository_url && (
          <a
            href={project.repository_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm border rounded-lg px-3 py-1.5 bg-white shadow-sm flex items-center gap-2 hover:text-primary transition-all self-start md:self-auto"
          >
            <GitCommit className="h-4 w-4" />
            Repository Link
          </a>
        )}
      </div>

      {/* Tabs Command Center */}
      <Tabs defaultValue="upload" className="w-full">
        <TabsList className="grid w-full grid-cols-4 glass border p-1 rounded-lg">
          <TabsTrigger value="upload" className="font-semibold">BRD Upload & Extract</TabsTrigger>
          <TabsTrigger value="summary" className="font-semibold">AI Executive Summary</TabsTrigger>
          <TabsTrigger value="versions" className="font-semibold">Version History</TabsTrigger>
          <TabsTrigger value="review" className="font-semibold">Client Review</TabsTrigger>
        </TabsList>

        {/* BRD Upload & Extracted Requirements */}
        <TabsContent value="upload" className="mt-4">
          <div className="grid gap-6 md:grid-cols-3">
            {/* Upload Zone */}
            <Card className="glass md:col-span-1 border border-white/20">
              <CardHeader>
                <CardTitle className="text-lg">Upload BRD Document</CardTitle>
                <CardDescription>
                  Upload your Business Requirement Document (PDF or DOCX) to extract and baseline development tracks.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div
                  onDragEnter={handleDrag}
                  onDragOver={handleDrag}
                  onDragLeave={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-300 ${
                    dragActive
                      ? "border-primary bg-primary/5"
                      : "border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/10"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".pdf,.docx"
                    onChange={handleFileChange}
                    disabled={uploading}
                  />
                  <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                  <p className="text-sm font-semibold mb-1">
                    Drag & drop file here
                  </p>
                  <p className="text-xs text-muted-foreground">
                    or click to browse files (PDF, DOCX)
                  </p>
                </div>

                {uploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span>Uploading & parsing document...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Extracted Requirements View */}
            <Card className="glass md:col-span-2 border border-white/20">
              <CardHeader>
                <CardTitle className="text-lg">Extracted System Requirements</CardTitle>
                <CardDescription>
                  List of system requirements deterministically parsed from the BRD source.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {versions.length === 0 ? (
                  <div className="text-center p-12 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto text-muted-foreground/30 mb-3" />
                    <p className="text-sm">No requirements parsed yet. Upload a BRD document to start extraction.</p>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                    {versions.map((ver) => (
                      <div
                        key={ver.id}
                        className="p-4 border rounded-lg hover:border-primary/30 bg-muted/5 transition-all flex flex-col gap-2"
                      >
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <span className="font-bold text-sm tracking-tight text-foreground">
                            Version {ver.version_number}.0
                          </span>
                          <div className="flex items-center gap-2">
                            <Badge className={
                              ver.status === "Approved" ? "bg-green-100 text-green-800" :
                              ver.status === "Changes Requested" ? "bg-red-100 text-red-800" :
                              "bg-amber-100 text-amber-800"
                            }>
                              {ver.status}
                            </Badge>
                            {ver.is_baseline && (
                              <Badge className="bg-primary/20 text-primary-foreground border-primary/30 flex items-center gap-1">
                                <Lock className="h-3 w-3" />
                                Baseline
                              </Badge>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-foreground bg-white p-2.5 rounded border leading-relaxed whitespace-pre-wrap">
                          {ver.content}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI Executive Summary */}
        <TabsContent value="summary" className="mt-4">
          <Card className="glass border border-white/20">
            <CardHeader className="flex flex-row items-center justify-between gap-4 flex-wrap">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  AI executive analysis
                </CardTitle>
                <CardDescription>
                  Synthesized product summary, context flow, and core feature definitions compiled from requirements.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {versions.length === 0 ? (
                <div className="text-center p-12 text-muted-foreground">
                  <Sparkles className="h-12 w-12 mx-auto text-primary/30 mb-3" />
                  <p className="text-sm">No analysis reports available. Upload a BRD document first.</p>
                </div>
              ) : (
                <div className="grid gap-6">
                  {versions.filter(v => v.ai_summary).map((ver) => (
                    <div key={ver.id} className="p-5 border rounded-xl bg-white shadow-sm space-y-4">
                      <div className="flex items-center justify-between border-b pb-2">
                        <span className="font-bold text-sm text-muted-foreground flex items-center gap-2">
                          <History className="h-4 w-4 text-primary" />
                          Version {ver.version_number}.0 AI Analysis Summary
                        </span>
                        <Badge className="bg-primary/10 text-primary">Generated</Badge>
                      </div>
                      <div className="prose prose-sm max-w-none text-foreground whitespace-pre-wrap leading-relaxed">
                        {ver.ai_summary}
                      </div>
                    </div>
                  ))}
                  
                  {versions.filter(v => v.ai_summary).length === 0 && (
                    <div className="p-8 border rounded-lg text-center bg-muted/10 text-muted-foreground">
                      <p>AI summaries are processing or were not successfully generated for these items.</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Version History & Timeline */}
        <TabsContent value="versions" className="mt-4">
          <Card className="glass border border-white/20">
            <CardHeader>
              <CardTitle className="text-lg">Requirement Version Timeline</CardTitle>
              <CardDescription>
                Chronological updates, baselines, and changes generated for this project.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {versions.length === 0 ? (
                <div className="text-center p-12 text-muted-foreground">
                  <History className="h-12 w-12 mx-auto text-muted-foreground/30 mb-3" />
                  <p className="text-sm">Timeline is empty. Start by uploading a requirement document.</p>
                </div>
              ) : (
                <div className="relative pl-6 border-l-2 border-primary/20 space-y-8 py-2 ml-4">
                  {versions.map((ver) => (
                    <div key={ver.id} className="relative">
                      {/* Timeline Dot */}
                      <span className="absolute -left-[31px] top-1.5 flex h-4.5 w-4.5 items-center justify-center rounded-full bg-white border-2 border-primary">
                        <Clock className="h-3 w-3 text-primary" />
                      </span>
                      <div className="flex flex-col gap-1 p-4 border rounded-lg bg-white shadow-xs">
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <span className="font-bold text-md text-foreground">
                            Requirement Update (v{ver.version_number}.0)
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(ver.created_at || Date.now()).toLocaleDateString()}
                          </span>
                        </div>
                        {ver.change_summary && (
                          <p className="text-sm italic text-muted-foreground mt-1 bg-amber-50/50 p-2 rounded border border-amber-100">
                            <strong>Reason for change:</strong> {ver.change_summary}
                          </p>
                        )}
                        <p className="text-sm text-foreground mt-2 line-clamp-3">
                          {ver.content}
                        </p>
                        <div className="flex gap-2 items-center mt-3">
                          <Badge variant="outline">{ver.status}</Badge>
                          {ver.is_baseline && (
                            <Badge className="bg-green-100 text-green-800 flex items-center gap-1">
                              <CheckCircle className="h-3 w-3" />
                              Baseline Locked
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Client Review & Approvals */}
        <TabsContent value="review" className="mt-4">
          <Card className="glass border border-white/20">
            <CardHeader>
              <CardTitle className="text-lg">Client Approval Desk</CardTitle>
              <CardDescription>
                Review outstanding system specifications and lock in baselines to secure implementation alignment.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {versions.length === 0 ? (
                <div className="text-center p-12 text-muted-foreground">
                  <UserCheck className="h-12 w-12 mx-auto text-muted-foreground/30 mb-3" />
                  <p className="text-sm">No items found to review.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {versions.map((ver) => (
                    <div key={ver.id} className="p-5 border rounded-lg bg-white shadow-sm space-y-4">
                      <div className="flex items-center justify-between gap-4 border-b pb-2 flex-wrap">
                        <span className="font-bold text-sm text-foreground">
                          Requirement Version {ver.version_number}.0
                        </span>
                        <div className="flex items-center gap-2">
                          <Badge className={
                            ver.status === "Approved" ? "bg-green-100 text-green-800" :
                            ver.status === "Changes Requested" ? "bg-red-100 text-red-800" :
                            "bg-amber-100 text-amber-800"
                          }>
                            {ver.status}
                          </Badge>
                          {ver.is_baseline && (
                            <Badge className="bg-primary/20 text-primary-foreground">
                              Locked Baseline
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="bg-muted/10 p-3.5 rounded border text-sm max-h-[150px] overflow-y-auto whitespace-pre-wrap">
                        {ver.content}
                      </div>

                      {ver.status === "Pending Review" && (
                        <div className="space-y-3 pt-2">
                          <div className="grid gap-1.5">
                            <Label htmlFor={`comment-${ver.id}`} className="text-xs font-semibold">
                              Review Feedback Comment (Optional)
                            </Label>
                            <Input
                              id={`comment-${ver.id}`}
                              placeholder="e.g. Looks good, or please refine heading structure."
                              value={comment}
                              onChange={(e) => setComment(e.target.value)}
                            />
                          </div>
                          <div className="flex gap-2 justify-end">
                            <Button
                              variant="outline"
                              className="text-red-600 hover:bg-red-50 hover:text-red-700"
                              onClick={() => handleReview(ver.id, "request_changes")}
                              disabled={actionLoading === ver.id}
                            >
                              {actionLoading === ver.id && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                              Request Changes
                            </Button>
                            <Button
                              className="bg-green-600 hover:bg-green-700 text-white"
                              onClick={() => handleReview(ver.id, "approve")}
                              disabled={actionLoading === ver.id}
                            >
                              {actionLoading === ver.id && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                              Approve & Baseline
                            </Button>
                          </div>
                        </div>
                      )}
                      
                      {ver.status === "Approved" && (
                        <div className="flex items-center gap-2 text-green-700 text-xs bg-green-50 p-2.5 rounded border border-green-100 font-semibold">
                          <CheckCircle className="h-4 w-4" />
                          This requirement version has been approved and locked as a production baseline.
                        </div>
                      )}

                      {ver.status === "Changes Requested" && (
                        <div className="flex items-center gap-2 text-red-700 text-xs bg-red-50 p-2.5 rounded border border-red-100 font-semibold">
                          <AlertCircle className="h-4 w-4" />
                          Changes requested. Please modify content in the editor/document and upload a new version.
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
