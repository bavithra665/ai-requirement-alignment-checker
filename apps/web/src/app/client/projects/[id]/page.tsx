"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { AlertCircle, CheckCircle, Clock } from "lucide-react";
import { api } from "@/lib/api-client";

interface RequirementVersion {
  id: string;
  requirement_id: string;
  version_number: number;
  content: string;
  status: string;
  is_baseline: boolean;
  created_at: string;
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
  const [action, setAction] = useState<"approve" | "reject" | null>(null);

  useEffect(() => {
    loadVersions();
    // loadVersions is stable in this scope; disabling exhaustive-deps for clarity
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const loadVersions = async () => {
    try {
      setIsLoading(true);
      const data = await api.client.getRequirementVersions(projectId);
      setVersions(data);
      if (data.length > 0) {
        setSelectedVersion(data[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load versions");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedVersion) return;
    setIsSubmitting(true);
    try {
      await api.client.approveRequirementVersion(projectId, selectedVersion.id, comment);
      setAction(null);
      setComment("");
      loadVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!selectedVersion) return;
    setIsSubmitting(true);
    try {
      await api.client.rejectRequirementVersion(projectId, selectedVersion.id, comment);
      setAction(null);
      setComment("");
      loadVersions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Requirement Review</h1>
        <p className="text-muted-foreground">
          Review requirement versions and provide your approval
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
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Loading requirements...</p>
          </CardContent>
        </Card>
      ) : versions.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">No requirements available for review.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Version List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Requirement Versions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-96 overflow-y-auto">
                {versions.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => setSelectedVersion(v)}
                    className={`w-full text-left p-3 rounded-md border transition-all ${
                      selectedVersion?.id === v.id
                        ? "border-primary bg-primary/5"
                        : "border-muted hover:border-primary/50"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-sm">v{v.version_number}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(v.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {v.status === "approved" && (
                        <CheckCircle className="h-4 w-4 text-green-500 ml-2" />
                      )}
                      {v.status === "pending" && (
                        <Clock className="h-4 w-4 text-yellow-500 ml-2" />
                      )}
                    </div>
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Version Details */}
          <div className="lg:col-span-2 space-y-4">
            {selectedVersion && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>Current Version</CardTitle>
                    <CardDescription>
                      Version {selectedVersion.version_number} ({selectedVersion.status})
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="bg-muted p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Content</h4>
                      <p className="text-sm whitespace-pre-wrap">{selectedVersion.content}</p>
                    </div>

                    {selectedVersion.is_baseline && (
                      <div className="bg-green-50 dark:bg-green-950/20 p-3 rounded-lg flex items-start gap-2">
                        <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                        <div>
                          <p className="font-medium text-sm text-green-700 dark:text-green-400">
                            Approved Baseline
                          </p>
                          <p className="text-xs text-green-600 dark:text-green-400">
                            This is the current approved requirement baseline
                          </p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Action Buttons */}
                {!selectedVersion.is_baseline && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Your Action</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <Label htmlFor="comment" className="mb-2">
                          Comment (Optional)
                        </Label>
                        <textarea
                          id="comment"
                          placeholder="Add a comment..."
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                          className="w-full p-3 rounded border"
                        />
                      </div>

                      <div className="flex gap-2">
                        <Button onClick={() => setAction('approve')} disabled={isSubmitting} className="bg-green-600 text-white">
                          Approve
                        </Button>
                        <Button onClick={() => setAction('reject')} disabled={isSubmitting} className="bg-amber-500 text-white">
                          Request Changes
                        </Button>
                      </div>

                      {action === 'approve' && (
                        <div className="flex gap-2 mt-2">
                          <Button onClick={handleApprove} disabled={isSubmitting} className="bg-green-600 text-white">
                            Confirm Approve
                          </Button>
                          <Button variant="ghost" onClick={() => setAction(null)} disabled={isSubmitting}>
                            Cancel
                          </Button>
                        </div>
                      )}

                      {action === 'reject' && (
                        <div className="flex gap-2 mt-2">
                          <Button onClick={handleReject} disabled={isSubmitting} className="bg-amber-500 text-white">
                            Confirm Request Changes
                          </Button>
                          <Button variant="ghost" onClick={() => setAction(null)} disabled={isSubmitting}>
                            Cancel
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
