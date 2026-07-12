"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldCheck, ChevronRight, FileCheck2 } from "lucide-react";
import { api } from "@/lib/api-client";
import { useAuth } from "@/context/auth";

type LoginStep = "role-selection" | "form";
type UserRole = "developer" | "client";

export default function LoginPage() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState<LoginStep>("role-selection");
  const [role, setRole] = useState<UserRole | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRoleSelect = (selectedRole: UserRole) => {
    setRole(selectedRole);
    setStep("form");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      await api.login(formData);

      // Get user info to check role
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const apiBaseUrl = base.endsWith("/api/v1") ? base : `${base}/api/v1`;
      const response = await fetch(`${apiBaseUrl}/auth/me`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const user = await response.json();

        // Role mismatch check: if the account role doesn't match the selected portal
        if (user.role !== role) {
          // Clear the token immediately — this account doesn't belong here
          localStorage.removeItem("token");
          setError(
            `No ${role} account found for this email. Please register as a ${role} or sign in via the correct portal.`
          );
          setIsLoading(false);
          return;
        }

        // Refresh auth context only after role is confirmed
        await refreshUser();

        if (user.role === "client") {
          router.push("/client/dashboard");
        } else {
          router.push("/dashboard");
        }
      } else {
        setError("Login failed. Please check your credentials.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] p-4">
      {step === "role-selection" ? (
        <div className="w-full max-w-2xl">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-2 mb-4">
              <div className="h-8 w-8 rounded bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <FileCheck2 className="h-5 w-5 text-white" />
              </div>
              <span className="text-2xl font-bold text-slate-900 tracking-tight">AlignmentChecker</span>
            </div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">Welcome Back</h1>
            <p className="text-slate-500">Sign in to your account to continue</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Developer Card */}
            <div
              onClick={() => handleRoleSelect("developer")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") handleRoleSelect("developer");
              }}
              className="group cursor-pointer transform hover:-translate-y-1 transition-all duration-300"
            >
              <Card className="border-2 border-cyan-400 bg-white/80 backdrop-blur-md shadow-lg shadow-cyan-400/20 hover:shadow-xl hover:shadow-cyan-400/40 hover:border-cyan-300 transition-all cursor-pointer h-full" style={{boxShadow: '0 0 18px rgba(34,211,238,0.25)'}}>
                <CardHeader>
                  <CardTitle className="text-2xl font-extrabold text-slate-900 tracking-tight">Developer Sign In</CardTitle>
                  <CardDescription className="text-slate-500">
                    Access project tools and requirement alignments
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-slate-600 text-sm">
                  <div className="flex items-center justify-center py-6">
                     <div className="h-16 w-16 bg-blue-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                        <ShieldCheck className="h-8 w-8 text-blue-500" />
                     </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-md shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all">
                    Sign in as Developer <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardFooter>
              </Card>
            </div>

            {/* Client Card */}
            <div
              onClick={() => handleRoleSelect("client")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") handleRoleSelect("client");
              }}
              className="group cursor-pointer transform hover:-translate-y-1 transition-all duration-300"
            >
              <Card className="border-2 border-cyan-400 bg-white/80 backdrop-blur-md shadow-lg shadow-cyan-400/20 hover:shadow-xl hover:shadow-cyan-400/40 hover:border-cyan-300 transition-all cursor-pointer h-full" style={{boxShadow: '0 0 18px rgba(34,211,238,0.25)'}}>
                <CardHeader>
                  <CardTitle className="text-2xl font-extrabold text-slate-900 tracking-tight">Client Sign In</CardTitle>
                  <CardDescription className="text-slate-500">
                    Review progress and approve requirements
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 text-slate-600 text-sm">
                  <div className="flex items-center justify-center py-6">
                     <div className="h-16 w-16 bg-blue-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                        <FileCheck2 className="h-8 w-8 text-blue-500" />
                     </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-md shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all">
                    Sign in as Client <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardFooter>
              </Card>
            </div>
          </div>

          <div className="text-center mt-8">
            <p className="text-slate-500">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="text-blue-600 hover:text-blue-700 font-medium hover:underline">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      ) : (
        <Card className="w-full max-w-md bg-white/90 backdrop-blur-lg border-2 border-cyan-400 shadow-2xl animate-in fade-in zoom-in-95 duration-300" style={{boxShadow: '0 0 28px rgba(34,211,238,0.35)'}}>
          <CardHeader className="space-y-2 text-center">
            <div className="flex justify-center mb-4">
              <div className="h-14 w-14 bg-blue-50 rounded-full flex items-center justify-center shadow-inner">
                <ShieldCheck className="h-7 w-7 text-blue-500" />
              </div>
            </div>
            <CardTitle className="text-3xl font-bold tracking-tight text-slate-900">
              Welcome, {role === "developer" ? "Developer" : "Client"}
            </CardTitle>
            <CardDescription className="text-slate-500 text-base">
              Enter your credentials to access the alignment checker
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-5">
                {error && (
                  <div className="bg-red-50 text-red-500 border border-red-200 px-4 py-3 rounded-lg text-sm flex items-center animate-in slide-in-from-top-2">
                    <span className="font-medium">{error}</span>
                  </div>
                )}
                <div className="grid gap-2">
                  <Label htmlFor="email" className="text-slate-700 font-medium">Username or Email</Label>
                  <Input
                    id="email"
                    type="text"
                    placeholder="Enter username or email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    className="border-gray-300 focus-visible:ring-blue-500 h-11 transition-all duration-200"
                  />
                </div>
                <div className="grid gap-2">
                  <div className="flex items-center">
                    <Label htmlFor="password" className="text-slate-700 font-medium">Password</Label>
                    <a
                      href="#"
                      className="ml-auto inline-block text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline transition-colors"
                    >
                      Forgot password?
                    </a>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    className="border-gray-300 focus-visible:ring-blue-500 h-11 transition-all duration-200"
                  />
                </div>
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-11 text-base font-medium bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-md shadow-blue-500/25 hover:shadow-lg hover:shadow-blue-500/40 transition-all duration-300 mt-2"
                >
                  {isLoading ? "Signing in..." : "Sign In"}
                </Button>
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex justify-center border-t border-gray-100 mt-4 pt-6 pb-2">
            <button
              onClick={() => setStep("role-selection")}
              className="text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors flex items-center group"
            >
              <ChevronRight className="h-4 w-4 mr-1 rotate-180 group-hover:-translate-x-1 transition-transform" /> 
              Back to role selection
            </button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
}
