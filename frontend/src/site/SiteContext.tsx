import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/endpoints";
import type { SiteInfo } from "../api/types";

const DEFAULT_SITE: SiteInfo = {
  site_name: "Course Platform",
  currency: "RUB",
  demo_payments: false,
};

const SiteContext = createContext<SiteInfo>(DEFAULT_SITE);

export function SiteProvider({ children }: { children: ReactNode }) {
  const [site, setSite] = useState<SiteInfo>(DEFAULT_SITE);

  useEffect(() => {
    api.site().then(setSite).catch(() => setSite(DEFAULT_SITE));
  }, []);

  return <SiteContext value={site}>{children}</SiteContext>;
}

export function useSite(): SiteInfo {
  return useContext(SiteContext);
}

export function usePageTitle(title?: string): void {
  const { site_name } = useSite();
  useEffect(() => {
    document.title = title ? `${title} — ${site_name}` : site_name;
  }, [title, site_name]);
}
