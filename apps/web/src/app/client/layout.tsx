"use client";

import { ReactNode, useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { LogOut, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/auth";

const ELetter = () => (
  <span className="inline-flex flex-col justify-between h-[11px] w-[8.5px] py-[0.75px] mx-[0.5px] shrink-0 align-middle">
    <span className="h-[2px] w-full bg-current rounded-[1px]"></span>
    <span className="h-[2px] w-full bg-current rounded-[1px]"></span>
    <span className="h-[2px] w-full bg-current rounded-[1px]"></span>
  </span>
);

const PinesphereBrand = () => (
  <div className="flex items-center gap-2.5 select-none">
    <div 
      className="h-10 w-10 shrink-0 rounded-md shadow-sm" 
      style={{
        backgroundImage: "url('/pinesphere-logo.png')",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "center -3px",
        backgroundSize: "155% auto"
      }}
    />
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

export default function ClientLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { logout, user } = useAuth();

  const handleLogout = async () => {
    logout();
    router.push("/");
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
        <Link href="/client/dashboard" className="flex items-center gap-2 font-semibold">
          <PinesphereBrand />
        </Link>

        <div className="ml-auto flex items-center gap-4">
          <Button variant="ghost" size="icon" className="rounded-full">
            <Bell className="h-5 w-5 text-muted-foreground" />
            <span className="sr-only">Notifications</span>
          </Button>

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

      <main className="flex-1 p-4 sm:p-6">
        <div className="mx-auto max-w-6xl">
          {children}
        </div>
      </main>
    </div>
  );
}
