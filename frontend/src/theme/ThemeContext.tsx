import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/endpoints";
import type { ThemePreference } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const STORAGE_KEY = "course_platform_theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

interface ThemeState {
  preference: ThemePreference;
  setPreference: (preference: ThemePreference) => void;
}

const ThemeContext = createContext<ThemeState | null>(null);

function readStoredPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "dark" || stored === "system") return stored;
  } catch {
    return "light";
  }
  return "light";
}

function storePreference(preference: ThemePreference): void {
  try {
    localStorage.setItem(STORAGE_KEY, preference);
  } catch {
    return;
  }
}

function applyTheme(preference: ThemePreference): void {
  const dark =
    preference === "dark" || (preference === "system" && window.matchMedia(DARK_QUERY).matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [preference, setPreferenceState] = useState<ThemePreference>(readStoredPreference);

  useEffect(() => {
    if (user) setPreferenceState(user.theme);
  }, [user?.id]);

  useEffect(() => {
    applyTheme(preference);
    storePreference(preference);
    if (preference !== "system") return;
    const media = window.matchMedia(DARK_QUERY);
    const onChange = () => applyTheme("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [preference]);

  const setPreference = useCallback(
    (next: ThemePreference) => {
      setPreferenceState(next);
      if (user) api.auth.updateMe({ theme: next }).catch(() => undefined);
    },
    [user],
  );

  return <ThemeContext value={{ preference, setPreference }}>{children}</ThemeContext>;
}

export function useTheme(): ThemeState {
  const context = useContext(ThemeContext);
  if (context === null) throw new Error("useTheme must be used inside <ThemeProvider>");
  return context;
}
