import React, { createContext, useContext, useEffect, useState } from "react";
import { type UserProfile, loginUser, logoutUser, getCurrentUser } from "@/lib/api";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (operatorId: string, accessKey: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("consensus_user") : null;
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return typeof window !== "undefined" ? localStorage.getItem("consensus_token") : null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function initAuth() {
      const savedToken = localStorage.getItem("consensus_token");
      if (savedToken) {
        try {
          const profile = await getCurrentUser();
          if (profile) {
            setUser(profile);
            localStorage.setItem("consensus_user", JSON.stringify(profile));
          } else {
            // Token may have expired or is invalid
            setUser(null);
            setToken(null);
            localStorage.removeItem("consensus_token");
            localStorage.removeItem("consensus_user");
          }
        } catch {
          // If offline or error, keep local storage user for smooth demo
        }
      }
      setIsLoading(false);
    }
    initAuth();
  }, []);

  const handleLogin = async (operatorId: string, accessKey: string) => {
    setIsLoading(true);
    try {
      const res = await loginUser(operatorId, accessKey);
      setUser(res.user);
      setToken(res.token);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    setIsLoading(true);
    try {
      await logoutUser();
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login: handleLogin,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
