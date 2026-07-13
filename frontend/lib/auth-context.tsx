"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { setTokens, setStoredUser, getStoredUser, clearSession, getAccessToken } from "@/lib/api";

export type RadarUser = {
  id: string;
  email: string;
  name: string;
  role: "admin" | "manager" | "recruiter" | "executive";
};

type AuthContextType = {
  user: RadarUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<RadarUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const stored = getStoredUser<RadarUser>();
    const token = getAccessToken();
    if (stored && token) {
      setUser(stored);
    }
    setLoading(false);
  }, []);

  async function login(email: string, password: string) {
    const data = await api.post("/api/v1/auth/login", { email, password });
    setTokens(data);
    setStoredUser(data.user);
    setUser(data.user);
    router.push("/dashboard");
  }

  function logout() {
    clearSession();
    setUser(null);
    router.push("/auth");
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
