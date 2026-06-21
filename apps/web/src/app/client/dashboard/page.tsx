"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FolderOpen, AlertCircle, User, ClipboardCheck, FileText } from "lucide-react";
import { api } from "@/lib/api-client";
import { useAuth } from "@/context/auth";

interface Project {
  id: string;
  name: string;
  client_name: string;
  client_email?: string;
  description?: string;
  status: string;
  owner_id: string;
}

interface RequirementVersion {
  id: string;
  status: string;
}

interface ProjectStats {
  project: Project;
  ownerName: string;
  totalVersions: number;
  pendingApprovals: number;
  approvedCount: number;
}

export default function ClientDashboard() {
  const { user } = useAuth();
  const [projectStats, setProjectStats] = useState<ProjectStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setIsLoading(true);
      const projects = await api.client.getProjects() as Project[];

      const stats = await Promise.all(
        projects.map(async (project) => {
          let versions: RequirementVersion[] = [];
          try {
            versions = await api.client.getRequirementVersions(project.id) as RequirementVersion[];
          } catch {
            versions = [];
          }
          const pending = versions.filter(v =>
            v.status !== 'Approved' && v.status !== 'approved'
          ).length;
          const approved = versions.filter(v =>
            v.status === 'Approved' || v.status === 'approved'
          ).length;

          return {
            project,
            ownerName: "Developer",
            totalVersions: versions.length,
            pendingApprovals: pending,
            approvedCount: approved,
          };
        })
      );

      setProjectStats(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-1">Client Dashboard</h1>
        <p className="text-muted-foreground text-sm">
          Welcome back, <span className="font-semibold text-foreground">{user?.full_name || user?.email}</span>. Review and approve requirements for your assigned projects.
        </p>
      </div>

      {error && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="pt-6 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <Card key={i} className="animate-pulse">
              <CardHeader><div className="h-5 bg-muted rounded w-3/4" /></CardHeader>
              <CardContent><div className="space-y-2"><div className="h-4 bg-muted rounded" /><div className="h-4 bg-muted rounded w-2/3" /></div></CardContent>
            </Card>
          ))}
        </div>
      ) : projectStats.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <FolderOpen className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
            <p className="font-medium">No projects assigned yet</p>
            <p className="text-sm text-muted-foreground mt-1">Please contact your developer to be linked to a project.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projectStats.map(({ project, ownerName, totalVersions, pendingApprovals, approvedCount }) => (
            <Link key={project.id} href={`/client/projects/${project.id}`}>
              <Card className="hover:shadow-lg transition-all cursor-pointer h-full border hover:border-primary/40 group">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-base leading-tight group-hover:text-primary transition-colors truncate">
                        {project.name}
                      </CardTitle>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          project.status === 'Completed' ? 'bg-green-100 text-green-800' :
                          project.status === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                          'bg-amber-100 text-amber-800'
                        }`}>{project.status}</span>
                      </div>
                    </div>
                    <FolderOpen className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <User className="h-3.5 w-3.5" />
                    <span>Developer: <span className="font-medium text-foreground">{ownerName}</span></span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <div className="text-center p-2 bg-muted/50 rounded-md">
                      <p className="text-lg font-bold text-foreground">{totalVersions}</p>
                      <p className="text-xs text-muted-foreground flex items-center justify-center gap-1"><FileText className="h-3 w-3" />Reviews</p>
                    </div>
                    <div className="text-center p-2 bg-amber-50 rounded-md">
                      <p className="text-lg font-bold text-amber-700">{pendingApprovals}</p>
                      <p className="text-xs text-amber-600 flex items-center justify-center gap-1"><ClipboardCheck className="h-3 w-3" />Pending</p>
                    </div>
                    <div className="text-center p-2 bg-green-50 rounded-md">
                      <p className="text-lg font-bold text-green-700">{approvedCount}</p>
                      <p className="text-xs text-green-600 flex items-center justify-center gap-1"><ClipboardCheck className="h-3 w-3" />Approved</p>
                    </div>
                  </div>

                  <p className="text-xs text-muted-foreground text-right">Click to review requirements →</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
