"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle, XCircle, Clock } from "lucide-react";

import { api } from "@/lib/api-client";

interface ApprovalRequest {
  id: string;
  title: string;
  status: "pending" | "approved" | "rejected" | "requested_changes";
  clientName: string;
  comment?: string;
  createdAt: string;
}

export default function ApprovalsPage() {
  const [pending, setPending] = useState<ApprovalRequest[]>([]);
  const [requested, setRequested] = useState<ApprovalRequest[]>([]);
  const [rejected, setRejected] = useState<ApprovalRequest[]>([]);
  const [approved, setApproved] = useState<ApprovalRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    try {
      setIsLoading(true);
      const data: ApprovalRequest[] = await api.getApprovals();
      setPending(data.filter((a) => a.status === "pending"));
      setRequested(data.filter((a) => a.status === "requested_changes"));
      setRejected(data.filter((a) => a.status === "rejected"));
      setApproved(data.filter((a) => a.status === "approved"));
    } catch (error) {
      console.error("Failed to load approvals:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const renderApprovalCard = (approval: ApprovalRequest) => (
    <Card key={approval.id} className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{approval.title}</CardTitle>
            <CardDescription>By {approval.clientName}</CardDescription>
          </div>
          {approval.status === "requested_changes" && (
            <AlertCircle className="h-5 w-5 text-amber-500 ml-2" />
          )}
          {approval.status === "approved" && (
            <CheckCircle className="h-5 w-5 text-green-500 ml-2" />
          )}
          {approval.status === "rejected" && (
            <XCircle className="h-5 w-5 text-red-500 ml-2" />
          )}
        </div>
      </CardHeader>
      <CardContent>
        {approval.comment && (
          <div className="bg-muted p-3 rounded-md mb-4 text-sm">
            <p className="font-medium mb-1">Comment:</p>
            <p>{approval.comment}</p>
          </div>
        )}
        <Button variant="outline" className="w-full">
          View Version Details
        </Button>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Approval Requests</h1>
        <p className="text-muted-foreground">
          Track client approvals, rejection requests, and approved baselines
        </p>
      </div>

      {isLoading ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Loading approvals...</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-8">
          {/* Pending Approvals */}
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-500" />
              Pending Approvals
            </h2>
            {pending.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground text-sm">
                    No pending approvals. All versions are either approved or being reviewed.
                  </p>
                </CardContent>
              </Card>
            ) : (
              pending.map(renderApprovalCard)
            )}
          </div>

          {/* Requested Changes */}
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-amber-500" />
              Requested Changes
            </h2>
            {requested.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground text-sm">
                    No requested changes. All versions are approved or awaiting review.
                  </p>
                </CardContent>
              </Card>
            ) : (
              requested.map(renderApprovalCard)
            )}
          </div>

          {/* Rejected Versions */}
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <XCircle className="h-5 w-5 text-red-500" />
              Rejected Versions
            </h2>
            {rejected.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground text-sm">
                    No rejected versions. All versions are either approved or pending review.
                  </p>
                </CardContent>
              </Card>
            ) : (
              rejected.map(renderApprovalCard)
            )}
          </div>

          {/* Recently Approved */}
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Recently Approved
            </h2>
            {approved.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground text-sm">
                    No approved versions yet. Start by uploading requirements for client approval.
                  </p>
                </CardContent>
              </Card>
            ) : (
              approved.map(renderApprovalCard)
            )}
          </div>
        </div>
      )}
    </div>
  );
}
