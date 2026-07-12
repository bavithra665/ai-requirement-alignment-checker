"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { FileCheck2, ChevronRight, ShieldCheck } from "lucide-react";

type RegistrationStep = "role-selection" | "form";
type UserRole = "developer" | "client";

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<RegistrationStep>("role-selection");
  const [role, setRole] = useState<UserRole | null>(null);

  // Form state
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRoleSelect = (selectedRole: UserRole) => {
    setRole(selectedRole);
    setStep("form");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setIsLoading(true);

    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL}/auth/register`;
      console.log("Register URL:", url);
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          company_name: companyName,
          role,
        }),
      });

      if (response.ok) {
        router.push("/login?registered=true");
      } else {
        let data: { detail?: string } | null = null;
        try {
          data = await response.json();
        } catch {
          // ignore
        }
        setError(data?.detail || `Registration failed (HTTP ${response.status})`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
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
              <div className="h-8 w-8 rounded bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
                <FileCheck2 className="h-5 w-5 text-white" />
              </div>
              <span className="text-2xl font-bold text-slate-900">AlignmentChecker</span>
            </div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">Create Account</h1>
            <p className="text-slate-500">Choose your role to get started</p>
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
              className="group cursor-pointer"
            >
              <Card className="border-2 border-cyan-400 bg-white shadow-lg shadow-cyan-400/20 hover:shadow-xl hover:shadow-cyan-400/40 hover:border-cyan-300 transition-all cursor-pointer h-full" style={{boxShadow: '0 0 18px rgba(34,211,238,0.25)'}}>
                <CardHeader className="pb-4">
                  <CardTitle className="text-2xl font-extrabold text-slate-900 tracking-tight">Developer</CardTitle>
                  <CardDescription className="text-slate-500">
                    Manage requirements and implementations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center py-6">
                    <div className="h-16 w-16 bg-blue-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <ShieldCheck className="h-8 w-8 text-blue-500" />
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white group-hover:translate-x-1 transition-transform">
                    Choose Developer <ChevronRight className="ml-2 h-4 w-4" />
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
              className="group cursor-pointer"
            >
              <Card className="border-2 border-cyan-400 bg-white shadow-lg shadow-cyan-400/20 hover:shadow-xl hover:shadow-cyan-400/40 hover:border-cyan-300 transition-all cursor-pointer h-full" style={{boxShadow: '0 0 18px rgba(34,211,238,0.25)'}}>
                <CardHeader className="pb-4">
                  <CardTitle className="text-2xl font-extrabold text-slate-900 tracking-tight">Client</CardTitle>
                  <CardDescription className="text-slate-500">
                    Review and approve requirements
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-center py-6">
                    <div className="h-16 w-16 bg-blue-50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <FileCheck2 className="h-8 w-8 text-blue-500" />
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white group-hover:translate-x-1 transition-transform">
                    Choose Client <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardFooter>
              </Card>
            </div>
          </div>

          <div className="text-center mt-8">
            <p className="text-slate-500">
              Already have an account?{" "}
              <Link href="/login" className="text-blue-600 hover:text-blue-700 font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      ) : (
        <Card className="w-full max-w-md bg-white border-2 border-cyan-400 shadow-xl" style={{boxShadow: '0 0 28px rgba(34,211,238,0.35)'}}>
          <CardHeader className="space-y-2 text-center">
            <div className="flex justify-center mb-4">
              <div className="h-12 w-12 bg-primary/10 rounded-full flex items-center justify-center">
                <FileCheck2 className="h-6 w-6 text-primary" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight text-slate-900">
              Create {role === "developer" ? "Developer" : "Client"} Account
            </CardTitle>
            <CardDescription className="text-slate-500">
              Fill in your information to get started
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-4">
                {error && (
                  <div className="bg-red-50 text-red-500 border border-red-200 px-3 py-2 rounded-md text-sm">
                    {error}
                  </div>
                )}

                <div className="grid gap-2">
                  <Label htmlFor="fullName" className="text-slate-700">
                    Full Name
                  </Label>
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    disabled={isLoading}
                    className="border-gray-300 focus-visible:ring-primary"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="companyName" className="text-slate-700">
                    Company Name
                  </Label>
                  <Input
                    id="companyName"
                    type="text"
                    placeholder="Your Company"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    required
                    disabled={isLoading}
                    className="border-gray-300 focus-visible:ring-primary"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="email" className="text-slate-700">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    className="border-gray-300 focus-visible:ring-primary"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="password" className="text-slate-700">
                    Password
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="At least 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    className="border-gray-300 focus-visible:ring-primary"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="confirmPassword" className="text-slate-700">
                    Confirm Password
                  </Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    disabled={isLoading}
                    className="border-gray-300 focus-visible:ring-primary"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-primary hover:bg-secondary transition-all mt-2"
                >
                  {isLoading ? "Creating Account..." : "Create Account"}
                </Button>
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex justify-center">
            <button
              onClick={() => setStep("role-selection")}
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              ← Back to role selection
            </button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
}
