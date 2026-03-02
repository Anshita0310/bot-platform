import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Bot } from "lucide-react";
import { toast } from "sonner";

const Login = () => {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [orgId, setOrgId] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isSignup) {
        await signup(email, password, name, orgId);
        toast.success("Account created!");
      } else {
        await login(email, password);
      }
      navigate("/");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full bg-muted border border-border rounded-md px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary";

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-3 mb-8">
          <div className="bg-primary p-3 rounded-xl">
            <Bot size={28} className="text-primary-foreground" />
          </div>
          <h1 className="text-xl font-bold text-foreground">Bot Builder</h1>
          <p className="text-sm text-muted-foreground">
            {isSignup ? "Create your account" : "Sign in to your account"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-card border border-border rounded-xl p-6 space-y-4">
          {isSignup && (
            <>
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Name</label>
                <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" required />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Organization ID</label>
                <input className={inputClass} value={orgId} onChange={(e) => setOrgId(e.target.value)} placeholder="e.g. acme-corp" required />
              </div>
            </>
          )}
          <div>
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Email</label>
            <input className={inputClass} type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Password</label>
            <input className={inputClass} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {loading ? "Please wait..." : isSignup ? "Create Account" : "Sign In"}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground mt-4">
          {isSignup ? "Already have an account?" : "Don't have an account?"}{" "}
          <button onClick={() => setIsSignup(!isSignup)} className="text-primary hover:underline font-medium">
            {isSignup ? "Sign in" : "Sign up"}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;
