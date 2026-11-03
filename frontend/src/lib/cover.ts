const COVER_COLORS = ["#2F5D4E", "#A8432A", "#2B4C7E", "#8A6420", "#5B4A7A", "#3E6A73"];

function hash(text: string): number {
  let value = 0;
  for (const char of text) value = (value * 31 + (char.codePointAt(0) ?? 0)) >>> 0;
  return value;
}

export function coverColor(seed: string): string {
  return COVER_COLORS[hash(seed) % COVER_COLORS.length];
}

export function initials(title: string): string {
  return title
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() ?? "")
    .join("");
}
