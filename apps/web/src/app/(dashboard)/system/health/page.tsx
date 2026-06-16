"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Activity, Server, Database, BrainCircuit, GitBranch, Kanban, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ServiceHealth {
  status: "Green" | "Amber" | "Red";
  message: string;
}

interface SystemHealth {
  timestamp: string;
  services: Record<string, ServiceHealth>;
}

export default function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await api.getSystemHealth();
      setHealth(data);
      setError(null);
    } catch (error: unknown) { const errMsg = error instanceof Error ? error.message : String(error);
      setError(errMsg || "Failed to fetch system health");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Green":
        return "bg-green-100 text-green-800 border-green-200";
      case "Amber":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "Red":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getServiceIcon = (serviceKey: string) => {
    switch (serviceKey.toLowerCase()) {
      case "database":
        return <Database className="h-6 w-6 text-primary" />;
      case "chromadb":
        return <Server className="h-6 w-6 text-primary" />;
      case "groq":
        return <BrainCircuit className="h-6 w-6 text-primary" />;
      case "github":
        return <GitBranch className="h-6 w-6 text-primary" />;
      case "jira":
        return <Kanban className="h-6 w-6 text-primary" />;
      default:
        return <Activity className="h-6 w-6 text-primary" />;
    }
  };

  const formatServiceName = (name: string) => {
    const names: Record<string, string> = {
      database: "PostgreSQL",
      chromadb: "ChromaDB (Vector)",
      groq: "Groq LLM",
      github: "GitHub Integration",
      jira: "Jira Integration",
    };
    return names[name.toLowerCase()] || name;
  };

  return (
    <div className="grid gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent flex items-center gap-2">
            <Activity className="h-8 w-8 text-primary" />
            System Health
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Real-time status of critical infrastructure and third-party integrations.
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={fetchHealth} 
          disabled={loading}
          className="border-primary text-primary hover:bg-primary/10 transition-colors"
        >
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      {error ? (
        <Card className="glass border-red-200">
          <CardContent className="pt-6 flex flex-col items-center">
            <div className="text-red-500 mb-2">
              <Activity className="h-8 w-8" />
            </div>
            <p className="text-red-800 font-medium">{error}</p>
          </CardContent>
        </Card>
      ) : health ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(health.services).map(([key, service]) => (
            <Card key={key} className="glass hover:shadow-md transition-shadow border-t-4 border-t-primary">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-md font-semibold text-foreground flex items-center gap-2">
                  {getServiceIcon(key)}
                  {formatServiceName(key)}
                </CardTitle>
                <Badge variant="outline" className={getStatusColor(service.status)}>
                  {service.status}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="mt-2 text-sm text-muted-foreground">
                  <p>{service.message}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="flex justify-center items-center py-12 glass rounded-lg">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Checking system status...</span>
        </div>
      )}

      {health && (
        <div className="text-xs text-muted-foreground text-right">
          Last updated: {new Date(health.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
}
