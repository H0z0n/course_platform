import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/endpoints";
import type { SiteInfo } from "../api/types";
import { applyBrand } from "./brand";

const DEFAULT_SITE: SiteInfo = {
  site_name: "Course Platform",
  logo_url: null,
  accent_color: null,
  hero_badge: "Первые уроки — бесплатно",
  hero_title: "Учитесь в своём темпе —\nглава за главой",
  hero_text: null,
  currency: "RUB",
  demo_payments: false,
};

interface SiteState {
  site: SiteInfo;
  loaded: boolean;
  setSite: (site: SiteInfo) => void;
}

const SiteContext = createContext<SiteState>({
  site: DEFAULT_SITE,
  loaded: false,
  setSite: () => undefined,
});

export function SiteProvider({ children }: { children: ReactNode }) {
  const [site, setSite] = useState<SiteInfo>(DEFAULT_SITE);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api
      .site()
      .then(setSite)
      .catch(() => setSite(DEFAULT_SITE))
      .finally(() => setLoaded(true));
  }, []);

  useEffect(() => {
    if (loaded) applyBrand(site.accent_color, site.logo_url);
  }, [loaded, site.accent_color, site.logo_url]);

  return <SiteContext value={{ site, loaded, setSite }}>{children}</SiteContext>;
}

export function useSite(): SiteInfo {
  return useContext(SiteContext).site;
}

export function useSiteSettings(): SiteState {
  return useContext(SiteContext);
}

export function usePageTitle(title?: string): void {
  const { site_name } = useSite();
  useEffect(() => {
    document.title = title ? `${title} — ${site_name}` : site_name;
  }, [title, site_name]);
}
