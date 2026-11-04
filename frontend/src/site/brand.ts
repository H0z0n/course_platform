const STORAGE_KEY = "course_platform_brand";
const DEFAULT_ICON = "/favicon.svg";

function luminance(hex: string): number {
  const channels = [1, 3, 5].map((start) => {
    const value = parseInt(hex.slice(start, start + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

export function isLightColor(hex: string): boolean {
  return luminance(hex) > 0.2;
}

function remember(accent: string | null): void {
  try {
    if (accent) localStorage.setItem(STORAGE_KEY, accent);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    return;
  }
}

export function applyBrand(accent: string | null, logoUrl: string | null): void {
  const root = document.documentElement;
  if (accent) {
    root.style.setProperty("--brand", accent);
    root.dataset.brandTone = isLightColor(accent) ? "light" : "dark";
  } else {
    root.style.removeProperty("--brand");
    delete root.dataset.brandTone;
  }
  remember(accent);

  const icon = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
  if (icon) {
    icon.href = logoUrl ?? DEFAULT_ICON;
    if (logoUrl) icon.removeAttribute("type");
    else icon.type = "image/svg+xml";
  }
}
