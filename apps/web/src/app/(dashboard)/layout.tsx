import { ReactNode } from "react";
import { FileCheck2, LayoutDashboard, Settings, Users, LogOut, Bell, GitMerge, Zap, ShieldAlert, BarChart3, FileBarChart, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      {/* Topbar */}
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-white/80 glass px-4 sm:static sm:h-16 sm:border-0 sm:bg-transparent sm:px-6">
        <div className="flex items-center gap-2 font-semibold">
          <div className="h-8 w-8 rounded bg-primary flex items-center justify-center">
            <FileCheck2 className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl tracking-tight hidden sm:inline-block">AlignmentChecker</span>
        </div>
        
        <div className="ml-auto flex items-center gap-4">
          <Button variant="ghost" size="icon" className="rounded-full">
            <Bell className="h-5 w-5 text-muted-foreground" />
            <span className="sr-only">Toggle notifications</span>
          </Button>
          <div className="h-8 w-8 rounded-full bg-secondary text-white flex items-center justify-center font-medium">
            JD
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="fixed inset-y-0 left-0 z-10 hidden w-64 flex-col border-r bg-background sm:flex glass mt-16 shadow-sm">
          <nav className="flex flex-col gap-2 p-4 text-sm font-medium">
            <a
              href="/dashboard"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </a>
            <div className="px-3 py-2 text-xs font-semibold text-muted-foreground tracking-wider uppercase">
              Integrations
            </div>
            <a
              href="/integrations/jira"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <FileCheck2 className="h-4 w-4 text-sky-500" />
              Jira Sync
            </a>
            <a
              href="/integrations/github"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <Users className="h-4 w-4 text-teal-500" />
              GitHub PRs
            </a>
            <a
              href="/integrations/extraction"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <Settings className="h-4 w-4 text-indigo-500" />
              Code Extraction
            </a>
            <div className="px-3 py-2 text-xs font-semibold text-muted-foreground tracking-wider uppercase">
              AI Engine
            </div>
            <a
              href="/alignment"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <Zap className="h-4 w-4 text-amber-500" />
              Alignment Engine
            </a>
            <div className="px-3 py-2 text-xs font-semibold text-muted-foreground tracking-wider uppercase">
              Reports
            </div>
            <a
              href="/reports/mismatches"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <ShieldAlert className="h-4 w-4 text-amber-500" />
              Mismatch Reports
            </a>
            <a
              href="/reports/risk-dashboard"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <BarChart3 className="h-4 w-4 text-red-500" />
              Risk Dashboard
            </a>
            <a
              href="/reports/executive-summary"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <FileBarChart className="h-4 w-4 text-[#0096C7]" />
              Executive Report
            </a>
            <div className="px-3 py-2 text-xs font-semibold text-muted-foreground tracking-wider uppercase mt-2">
              System
            </div>
            <a
              href="/system/health"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <Activity className="h-4 w-4 text-green-600" />
              System Health
            </a>
          </nav>
          
          <div className="mt-auto p-4">
            <Button variant="outline" className="w-full justify-start gap-2 hover:bg-destructive/10 hover:text-destructive">
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 sm:pl-72 transition-all">
          <div className="mx-auto max-w-6xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
