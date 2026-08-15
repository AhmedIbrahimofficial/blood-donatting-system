/**
 * Minimal auth context.
 *
 * Stores the JWT access token in localStorage and exposes:
 *   - token       — current token (null = not logged in)
 *   - setToken()  — persist a new token after login
 *   - clearToken()— remove token on logout
 *   - isLoggedIn  — boolean convenience flag
 */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";

const TOKEN_KEY = "access_token";

interface AuthContextValue {
  token: string | null;
  isLoggedIn: boolean;
  setToken: (token: string) => void;
  clearToken: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() =>
    typeof localStorage !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null,
  );

  const setToken = useCallback((t: string) => {
    localStorage.setItem(TOKEN_KEY, t);
    setTokenState(t);
  }, []);

  const clearToken = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setTokenState(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ token, isLoggedIn: token !== null, setToken, clearToken }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
