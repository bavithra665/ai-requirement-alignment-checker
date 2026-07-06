"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { api } from "@/lib/api-client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FileCheck2, Users, Zap, BarChart3, ArrowRight, CheckCircle } from "lucide-react";

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

export default function Home() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

    if (token) {
      // User is logged in, use api helper which handles token refresh
      const checkRole = async () => {
        try {
          const user = await api.getMe();
          if (user?.role === "client") {
            router.push("/client/dashboard");
          } else {
            router.push("/dashboard");
          }
        } catch (error: unknown) {
          // If the API call fails (network, CORS, server down, or unauthenticated),
          // log nicely and fall back to showing the landing page (user can sign in).
          console.warn("Could not verify session with backend:", error);
        } finally {
          setIsChecking(false);
        }
      };
      checkRole();
    } else {
      setIsChecking(false);
    }
  }, [router]);

  if (isChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="text-center">
          <div className="inline-flex h-16 w-16 rounded-full bg-gradient-to-br from-blue-100 to-blue-50 items-center justify-center mb-4 shadow-inner shadow-blue-200">
            <FileCheck2 className="h-8 w-8 text-blue-600 animate-pulse" />
          </div>
          <p className="text-slate-500 font-medium tracking-wide">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-slate-900 relative overflow-hidden">
      {/* Background ambient glow effect using different blues */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-400/10 blur-[120px] pointer-events-none" />
      <div className="absolute top-[20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-400/10 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[20%] w-[60%] h-[60%] rounded-full bg-blue-600/5 blur-[150px] pointer-events-none" />

      {/* Navigation */}
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-gray-100/50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 font-bold">
            <PinesphereBrand />
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">
              Features
            </a>
            <Link href="/login">
              <Button variant="ghost" className="text-sm font-medium text-slate-600 hover:text-blue-600 hover:bg-blue-50">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-500 hover:from-blue-700 hover:via-blue-600 hover:to-cyan-600 text-white shadow-lg shadow-blue-500/25 border-0">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative max-w-7xl mx-auto px-6 pt-32 pb-24 text-center">
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 border border-blue-100 text-blue-700 text-sm font-semibold mb-8 shadow-sm">
            <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse"></span>
            AI-Powered Requirement Intelligence
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8">
            Align Requirements with
            <br />
            <span className="bg-gradient-to-r from-blue-700 via-blue-500 to-cyan-400 bg-clip-text text-transparent">
              Implementation
            </span>
          </h1>
          <p className="text-xl text-slate-500 mb-10 max-w-2xl mx-auto leading-relaxed">
            Ensure your requirements match your implementation across Jira, GitHub, and code artifacts. Catch mismatches before they reach production.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-20">
          <Link href="/register">
            <Button size="lg" className="bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-500 hover:from-blue-700 hover:via-blue-600 hover:to-cyan-600 text-white px-8 h-14 text-lg shadow-xl shadow-blue-500/20 border-0 rounded-xl group">
              Get Started <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline" className="border-gray-200 text-slate-700 hover:text-blue-700 hover:bg-blue-50/50 hover:border-blue-200 px-8 h-14 text-lg shadow-sm rounded-xl">
              Sign In
            </Button>
          </Link>
        </div>

        {/* Highlights */}
        <div className="grid md:grid-cols-3 gap-6 text-slate-600 font-medium mb-16 max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 bg-white/50 backdrop-blur-sm py-3 px-6 rounded-2xl border border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.4)]">
            <CheckCircle className="h-5 w-5 text-blue-500" />
            <span>AI-Powered Analysis</span>
          </div>
          <div className="flex items-center justify-center gap-3 bg-white/50 backdrop-blur-sm py-3 px-6 rounded-2xl border border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.4)]">
            <CheckCircle className="h-5 w-5 text-blue-500" />
            <span>Real-Time Collaboration</span>
          </div>
          <div className="flex items-center justify-center gap-3 bg-white/50 backdrop-blur-sm py-3 px-6 rounded-2xl border border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.4)]">
            <CheckCircle className="h-5 w-5 text-blue-500" />
            <span>Multi-Tool Integration</span>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-24 relative">
        <h2 className="text-3xl md:text-5xl font-extrabold text-center mb-16 text-slate-900 tracking-tight">Comprehensive Platform</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="group p-8 rounded-3xl border border-cyan-400 bg-white shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] transition-all duration-500 hover:-translate-y-2 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-100 to-transparent opacity-50 rounded-bl-full pointer-events-none group-hover:scale-110 transition-transform duration-500" />
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center mb-6 shadow-inner">
               <Zap className="h-7 w-7 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-900">AI-Powered Analysis</h3>
            <p className="text-slate-500 leading-relaxed">Automatically analyze alignment between requirements and implementation using advanced AI models with pinpoint accuracy.</p>
          </div>
          
          <div className="group p-8 rounded-3xl border border-cyan-400 bg-white shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] transition-all duration-500 hover:-translate-y-2 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyan-100 to-transparent opacity-50 rounded-bl-full pointer-events-none group-hover:scale-110 transition-transform duration-500" />
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-cyan-50 to-cyan-100 flex items-center justify-center mb-6 shadow-inner">
               <Users className="h-7 w-7 text-cyan-600" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-900">Team Collaboration</h3>
            <p className="text-slate-500 leading-relaxed">Seamlessly collaborate with developers and clients. Get approvals, request changes, and track requirements in real-time.</p>
          </div>
          
          <div className="group p-8 rounded-3xl border border-cyan-400 bg-white shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:shadow-[0_0_30px_rgba(34,211,238,0.5)] transition-all duration-500 hover:-translate-y-2 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-200 to-transparent opacity-30 rounded-bl-full pointer-events-none group-hover:scale-110 transition-transform duration-500" />
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center mb-6 shadow-inner">
               <BarChart3 className="h-7 w-7 text-blue-700" />
            </div>
            <h3 className="text-xl font-bold mb-3 text-slate-900">Risk Insights</h3>
            <p className="text-slate-500 leading-relaxed">Get actionable insights on requirement mismatches, implementation risks, and health metrics with detailed beautiful reports.</p>
          </div>
        </div>
      </section>

      {/* Integrations Section */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <h2 className="text-2xl font-bold text-center mb-12 text-slate-400 tracking-wider uppercase text-sm">Integrates with your stack</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {["Jira", "GitHub", "Code Artifacts", "AI Alignment"].map((tool) => (
            <div key={tool} className="py-8 px-6 rounded-2xl border border-cyan-400 bg-white/50 backdrop-blur text-slate-600 shadow-[0_0_15px_rgba(34,211,238,0.4)] hover:shadow-[0_0_25px_rgba(34,211,238,0.6)] hover:border-cyan-300 transition-all cursor-pointer font-semibold">
              {tool}
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-5xl mx-auto px-6 py-24">
        <div className="bg-gradient-to-br from-blue-600 via-blue-500 to-cyan-500 rounded-[2.5rem] p-12 md:p-20 text-center shadow-2xl shadow-blue-500/30 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-[40rem] h-[40rem] bg-white opacity-10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />
          <h2 className="text-4xl md:text-5xl font-extrabold mb-6 text-white tracking-tight relative z-10">Ready to Align Your Requirements?</h2>
          <p className="text-xl text-blue-50 mb-10 font-medium relative z-10 max-w-2xl mx-auto">Start today and catch mismatches before they cost you time and money.</p>
          <Link href="/register" className="relative z-10">
            <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-50 hover:text-blue-700 px-10 h-14 text-lg shadow-xl border-0 rounded-xl font-bold group">
              Get Started Now <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col md:flex-row justify-between items-center text-slate-500 text-sm font-medium">
          <p>&copy; 2026 AlignmentChecker. Powering requirement-to-implementation alignment.</p>
          <div className="flex gap-6 mt-4 md:mt-0">
            <a href="#" className="hover:text-blue-600 transition-colors">Privacy</a>
            <a href="#" className="hover:text-blue-600 transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
