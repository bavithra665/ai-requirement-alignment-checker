"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { 
  FolderPlus, 
  ArrowRight, 
  Folder, 
  Loader2, 
  ExternalLink,
  Code2,
  CheckCircle2,
  AlertCircle,
  Sparkles
} from "lucide-react";
import { api, Project } from "@/lib/api-client";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seedingDemo, setSeedingDemo] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [clientName, setClientName] = useState("");
  const [description, setDescription] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [jiraKey, setJiraKey] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects();
      setProjects(data);
      setError(null);
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      console.error(errMsg);
      setError("Failed to load projects. Ensure backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setSubmitting(true);
      await api.createProject({
        name,
        client_name: clientName || undefined,
        description: description || undefined,
        repository_url: repoUrl || undefined,
        jira_project_key: jiraKey || undefined,
      });
      
      // Reset form
      setName("");
      setClientName("");
      setDescription("");
      setRepoUrl("");
      setJiraKey("");
      setIsDialogOpen(false);
      
      // Refresh
      fetchProjects();
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      alert(errMsg || "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSeedDemo = async () => {
    try {
      setSeedingDemo(true);
      const res = await api.seedDemoWorkspace();
      await fetchProjects();
      if (res.project && res.project.id) {
        router.push(`/projects/${res.project.id}`);
      }
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      alert(errMsg || "Failed to seed demo workspace");
    } finally {
      setSeedingDemo(false);
    }
  };

  const draftCount = projects.filter(p => p.status === "Draft").length;
  const inProgressCount = projects.filter(p => p.status === "In Progress").length;
  const completedCount = projects.filter(p => p.status === "Completed").length;

  return (
    <div className="grid gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Workspace Dashboard
          </h1>
          <p className="text-muted-foreground text-sm">
            Manage your project alignment, upload BRDs, and analyze requirements.
          </p>
        </div>

        <div className="flex gap-2">
          <Button 
            variant="outline" 
            className="border-primary text-primary hover:bg-primary/10"
            onClick={handleSeedDemo}
            disabled={seedingDemo}
          >
            {seedingDemo ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
            Create Demo Workspace
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger>
              <div className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-10 px-4 py-2 bg-primary hover:bg-secondary text-white shadow-md cursor-pointer">
                <FolderPlus className="mr-2 h-4 w-4" />
                New Project
              </div>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px] glass border border-white/20">
            <form onSubmit={handleCreateProject}>
              <DialogHeader>
                <DialogTitle className="text-xl font-bold">Create Project</DialogTitle>
                <DialogDescription>
                  Start a new alignment project. Fill in details to associate requirements and repository targets.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Project Name *</Label>
                  <Input 
                    id="name" 
                    placeholder="e.g. Core Checkout API Redesign" 
                    value={name} 
                    onChange={e => setName(e.target.value)} 
                    required 
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="clientName">Client Name</Label>
                  <Input 
                    id="clientName" 
                    placeholder="e.g. Acme Corporation" 
                    value={clientName} 
                    onChange={e => setClientName(e.target.value)} 
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Input 
                    id="description" 
                    placeholder="Brief summary of project objectives" 
                    value={description} 
                    onChange={e => setDescription(e.target.value)} 
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="repoUrl">Repository URL</Label>
                    <Input 
                      id="repoUrl" 
                      placeholder="https://github.com/..." 
                      value={repoUrl} 
                      onChange={e => setRepoUrl(e.target.value)} 
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="jiraKey">Jira Project Key</Label>
                    <Input 
                      id="jiraKey" 
                      placeholder="e.g. CORE" 
                      value={jiraKey} 
                      onChange={e => setJiraKey(e.target.value.toUpperCase())} 
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setIsDialogOpen(false)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="bg-primary hover:bg-secondary text-white" 
                  disabled={submitting}
                >
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create Project
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
      </div>

      {/* Analytics Info Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="glass border-l-4 border-l-primary shadow-sm hover:shadow-md transition-all">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress Projects</CardTitle>
            <Folder className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{inProgressCount}</div>
            <p className="text-xs text-muted-foreground">Requirements being implemented</p>
          </CardContent>
        </Card>
        <Card className="glass border-l-4 border-l-amber-500 shadow-sm hover:shadow-md transition-all">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Draft Projects</CardTitle>
            <AlertCircle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{draftCount}</div>
            <p className="text-xs text-muted-foreground">Awaiting BRD / requirement baseline</p>
          </CardContent>
        </Card>
        <Card className="glass border-l-4 border-l-green-500 shadow-sm hover:shadow-md transition-all">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Projects</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedCount}</div>
            <p className="text-xs text-muted-foreground">All requirements fully aligned</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold tracking-tight">All Projects</h2>
        
        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 glass rounded-lg border border-dashed min-h-[200px]">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
            <p className="text-sm text-muted-foreground">Fetching project list...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center p-8 glass rounded-lg border border-red-200 text-center">
            <AlertCircle className="h-8 w-8 text-destructive mb-2" />
            <p className="text-sm font-medium text-destructive mb-1">{error}</p>
            <Button onClick={fetchProjects} variant="outline" size="sm">Try Again</Button>
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 glass rounded-lg border border-dashed text-center">
            <Folder className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-bold text-lg">No projects found</h3>
            <p className="text-sm text-muted-foreground mb-4 max-w-sm">
              Create your first project to get started with requirement uploading and AI analysis.
            </p>
            <Button onClick={() => setIsDialogOpen(true)} className="bg-primary hover:bg-secondary text-white">
              Create Project
            </Button>
          </div>
        ) : (
          <div className="glass border rounded-lg overflow-hidden">
            <Table>
              <TableHeader className="bg-muted/30">
                <TableRow>
                  <TableHead className="font-bold">Project Name</TableHead>
                  <TableHead className="font-bold">Client</TableHead>
                  <TableHead className="font-bold">Jira Key</TableHead>
                  <TableHead className="font-bold">Repository</TableHead>
                  <TableHead className="font-bold">Status</TableHead>
                  <TableHead className="w-[100px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((project) => (
                  <TableRow key={project.id} className="hover:bg-muted/10 transition-colors">
                    <TableCell className="font-semibold text-foreground">
                      <Link href={`/projects/${project.id}`} className="hover:text-primary transition-colors">
                        {project.name}
                      </Link>
                      {project.description && (
                        <p className="text-xs text-muted-foreground font-normal line-clamp-1">
                          {project.description}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>{project.client_name || <span className="text-muted-foreground text-xs italic">None</span>}</TableCell>
                    <TableCell>
                      {project.jira_project_key ? (
                        <Badge variant="outline" className="font-mono bg-blue-50/50 text-blue-700 dark:text-blue-400">
                          {project.jira_project_key}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-xs italic">Unmapped</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {project.repository_url ? (
                        <a 
                          href={project.repository_url} 
                          target="_blank" 
                          rel="noreferrer"
                          className="text-xs text-muted-foreground flex items-center gap-1 hover:text-primary transition-colors max-w-[200px] truncate"
                        >
                          <Code2 className="h-3 w-3 inline shrink-0" />
                          {project.repository_url.replace("https://github.com/", "")}
                          <ExternalLink className="h-3 w-3 inline shrink-0" />
                        </a>
                      ) : (
                        <span className="text-muted-foreground text-xs italic">No Repository</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        project.status === "Completed" ? "bg-green-100 text-green-800 hover:bg-green-200" :
                        project.status === "In Progress" ? "bg-blue-100 text-blue-800 hover:bg-blue-200" :
                        "bg-amber-100 text-amber-800 hover:bg-amber-200"
                      }>
                        {project.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Link href={`/projects/${project.id}`}>
                        <Button variant="ghost" size="sm" className="hover:bg-primary/10 hover:text-primary">
                          Open
                          <ArrowRight className="ml-1 h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}
