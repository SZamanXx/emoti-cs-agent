import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Sparkles, LogIn } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { signIn, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState("operator");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await signIn(username, password);
      const redirect = (location.state as { from?: string } | null)?.from || "/inbox";
      navigate(redirect, { replace: true });
    } catch (err) {
      setError((err as Error).message || "Login failed");
    }
  };

  return (
    <div className="min-h-screen grid place-items-center px-6">
      <div className="w-full max-w-md flex flex-col gap-5">
        <div className="flex items-center gap-2 justify-center">
          <Sparkles size={20} className="text-[color:var(--color-mint)]" />
          <div className="text-[15px] font-semibold tracking-tight">Emoti CS Agent</div>
        </div>
        <Card>
          <CardBody className="flex flex-col gap-4 p-7">
            <div>
              <h1 className="text-xl font-semibold tracking-tight">Operator console</h1>
              <p className="text-[13px] text-[color:var(--color-fg-muted)] mt-1">
                Zaloguj się żeby przeglądać tickety, edytować drafty i zarządzać killswitchami.
              </p>
            </div>

            <form className="flex flex-col gap-3" onSubmit={submit}>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>

              {error && (
                <div className="px-3 py-2 rounded border border-[color:var(--color-coral)]/40 bg-[color:var(--color-coral)]/10 text-[12.5px] text-[color:var(--color-coral)]">
                  {error}
                </div>
              )}

              <Button type="submit" disabled={loading || !password} className="mt-1">
                {loading ? "Logowanie…" : (<><LogIn size={14} /> Zaloguj</>)}
              </Button>
            </form>

            <div className="text-[11.5px] text-[color:var(--color-fg-dim)] leading-relaxed">
              Demo credentials: <code>operator</code> / <code>operator-demo-pwd</code> (configured via <code>OPERATOR_USERNAME</code> &amp; <code>OPERATOR_PASSWORD</code> in <code>backend/.env</code>). JWT issued by <code>POST /auth/login</code>, valid 24h.
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
