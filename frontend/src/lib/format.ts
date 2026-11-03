const pluralRules = new Intl.PluralRules("ru-RU");

export function formatPrice(price: string | null, currency: string): string {
  if (price === null) return "";
  const value = Number(price);
  if (value === 0) return "Бесплатно";
  const digits = Number.isInteger(value) ? 0 : 2;
  try {
    return new Intl.NumberFormat("ru-RU", {
      style: "currency",
      currency,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  } catch {
    return `${value} ${currency}`;
  }
}

export function plural(count: number, one: string, few: string, many: string): string {
  const form = pluralRules.select(count);
  const word = form === "one" ? one : form === "few" ? few : many;
  return `${count} ${word}`;
}

export function formatMinutes(minutes: number): string {
  if (minutes <= 0) return "";
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours === 0) return `≈ ${rest} мин`;
  return rest === 0 ? `≈ ${hours} ч` : `≈ ${hours} ч ${rest} мин`;
}

export function totalMinutes(lessons: { duration_minutes: number | null }[]): number {
  return lessons.reduce((sum, lesson) => sum + (lesson.duration_minutes ?? 0), 0);
}

const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];

export function roman(index: number): string {
  return ROMAN[index] ?? String(index + 1);
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function excerpt(markdown: string, length = 150): string {
  const plain = markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/[#>*_`|[\]()-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return plain.length > length ? `${plain.slice(0, length).trimEnd()}…` : plain;
}

export function normalizePrice(input: string): string | null {
  const cleaned = input.replace(/\s/g, "").replace(",", ".");
  return cleaned === "" ? null : cleaned;
}
