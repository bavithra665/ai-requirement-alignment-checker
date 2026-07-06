"use client";

import { ReactNode, useState, useRef, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FileCheck2, LayoutDashboard, Settings, Users, LogOut, Zap, ShieldAlert, BarChart3, FileBarChart, Activity, LucideIcon } from "lucide-react";
import { useAuth } from "@/context/auth";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";

type NavItem =
  | { href: string; label: string; icon: LucideIcon }
  | { section: string };

function buildNavItems(dashboardHref: string): NavItem[] {
  return [
    { href: dashboardHref, label: "Dashboard", icon: LayoutDashboard },
    { href: "/approvals", label: "Approval Requests", icon: FileCheck2 },
    { section: "Integrations" },
    { href: "/integrations/jira", label: "Jira Sync", icon: FileCheck2 },
    { href: "/integrations/github", label: "GitHub PRs", icon: Users },
    { href: "/integrations/extraction", label: "Code Extraction", icon: Settings },
    { section: "AI Engine" },
    { href: "/alignment", label: "Alignment Engine", icon: Zap },
    { section: "Reports" },
    { href: "/reports/mismatches", label: "Mismatch Reports", icon: ShieldAlert },
    { href: "/reports/risk-dashboard", label: "Risk Dashboard", icon: BarChart3 },
    { href: "/reports/executive-summary", label: "Executive Report", icon: FileBarChart },
    { section: "System" },
    { href: "/system/health", label: "System Health", icon: Activity },
  ];
}

function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

const ELetter = () => (
  <span className="inline-flex flex-col justify-between h-[11px] w-[8.5px] py-[0.75px] mx-[0.5px] shrink-0 align-middle">
    <span className="h-[2px] w-full bg-current rounded-[1px]"></span>
    <span className="h-[2px] w-full bg-current rounded-[1px]"></span>
    <span className="h-[2px] w-full bg-current rounded-[1px]"></span>
  </span>
);

const PinesphereBrand = () => (
  <div className="flex items-center gap-2.5 select-none">
    <div className="relative h-10 w-10 shrink-0 rounded-md overflow-hidden shadow-sm">
      <Image
        src="/pinesphere-logo.png"
        alt="Pinesphere logo"
        fill
        className="object-contain"
      />
    </div>
    <div className="hidden sm:flex items-center gap-2 leading-none">
      <span className="font-extrabold tracking-widest text-[15px] uppercase flex items-center shrink-0">
        <span className="text-[#3792d7] flex items-center">
          <span>P</span>
          <span>I</span>
          <span>N</span>
          <ELetter />
        </span>
        <span className="text-slate-800 flex items-center ml-[2px]">
          <span>S</span>
          <span>P</span>
          <span>H</span>
          <ELetter />
          <span>R</span>
          <ELetter />
        </span>
      </span>
      <span className="h-5 w-[1px] bg-slate-200 shrink-0" />
      <div className="flex flex-col text-[9px] font-bold text-slate-500 uppercase tracking-wider leading-tight shrink-0">
        <span>Requirement</span>
        <span>To Implementation</span>
      </div>
    </div>
  </div>
);

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();
  const dashboardHref = user?.role === 'client' ? '/client/dashboard' : '/dashboard';
  const navItems = buildNavItems(dashboardHref);

  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      {/* Topbar */}
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-white/80 glass px-4 sm:static sm:h-16 sm:border-0 sm:bg-transparent sm:px-6">
        <Link href={dashboardHref} className="flex items-center gap-2 font-semibold">
          <PinesphereBrand />
        </Link>
        
        <div className="ml-auto flex items-center gap-4">
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((o) => !o)}
              className="flex items-center gap-2 rounded-full px-3 py-1.5 hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-white flex items-center justify-center font-semibold text-sm shadow-md">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "?"}
              </div>
              <span className="text-sm font-semibold text-slate-800 hidden sm:block">
                {user?.full_name || "User"}
              </span>
              <svg className={`h-4 w-4 text-slate-500 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
            </button>
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-xl border border-slate-100 py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-4 py-2 border-b border-slate-100">
                  <p className="text-xs text-slate-400">Signed in as</p>
                  <p className="text-sm font-semibold text-slate-800 truncate">{user?.full_name || "User"}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="fixed inset-y-0 left-0 z-10 hidden w-64 flex-col border-r bg-background sm:flex glass mt-16 shadow-sm">
          <nav className="flex flex-col gap-2 p-4 text-sm font-medium">
            {navItems.map((item, index) =>
              "section" in item ? (
                <div
                  key={`section-${index}`}
                  className="px-3 py-1.5 text-xs font-bold text-white tracking-wider uppercase bg-[#48CAE4] rounded-md mt-2"
                >
                  {item.section}
                </div>
              ) : (
                <Link
                  key={item.href}
                  href={item.href}
                  className={
                    `flex items-center gap-3 rounded-lg px-3 py-2 transition-all ` +
                    (isActivePath(pathname ?? "", item.href)
                      ? "bg-primary/10 text-primary shadow-sm"
                      : "text-muted-foreground hover:text-primary")
                  }
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            )}
          </nav>
          
          <div className="mt-auto p-4">
            <Button
              variant="outline"
              className="w-full justify-start gap-2 hover:bg-destructive/10 hover:text-destructive"
              onClick={handleLogout}
            >
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
