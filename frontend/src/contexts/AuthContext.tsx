import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { authApi, type AuthResponse } from "@/lib/api";

interface User {
  email: string;
  name: string;
  orgId: string;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string, orgId: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadFromStorage(): { user: User | null; token: string | null } {
  const token = localStorage.getItem("token");
  const raw = localStorage.getItem("user");
  const user = raw ? (JSON.parse(raw) as User) : null;
  return { token, user };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => loadFromStorage().token);
  const [user, setUser] = useState<User | null>(() => loadFromStorage().user);

  const persist = useCallback((res: AuthResponse) => {
    localStorage.setItem("token", res.access_token);
    localStorage.setItem("user", JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await authApi.login({ email, password });
      persist(res);
    },
    [persist],
  );

  const signup = useCallback(
    async (email: string, password: string, name: string, orgId: string) => {
      const res = await authApi.signup({ email, password, name, orgId });
      persist(res);
    },
    [persist],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
