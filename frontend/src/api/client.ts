const TOKEN_KEY = "course_platform_token";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface ValidationIssue {
  loc?: (string | number)[];
  msg?: string;
}

let token = readStoredToken();
let handleUnauthorized: () => void = () => {};

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  return token;
}

export function setToken(value: string | null): void {
  token = value;
  try {
    if (value) localStorage.setItem(TOKEN_KEY, value);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    return;
  }
}

export function onUnauthorized(handler: () => void): void {
  handleUnauthorized = handler;
}

export function toApiError(reason: unknown): ApiError {
  if (reason instanceof ApiError) return reason;
  return new ApiError(0, reason instanceof Error ? reason.message : String(reason));
}

function describeIssue(issue: ValidationIssue): string {
  const message = (issue.msg ?? "некорректное значение").replace(/^Value error, /, "");
  const field = issue.loc?.filter((part) => part !== "body").join(".");
  return field ? `${field}: ${message}` : message;
}

function errorMessage(data: unknown, status: number): string {
  const detail = (data as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(describeIssue).join("; ");
  return `Ошибка сервера (${status})`;
}

export async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const sentToken = token;
  const headers: Record<string, string> = {};
  if (sentToken) headers.Authorization = `Bearer ${sentToken}`;

  let payload: BodyInit | undefined;
  if (body instanceof URLSearchParams) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`/api${path}`, { method, headers, body: payload });
  } catch {
    throw new ApiError(0, "Нет связи с сервером. Проверьте, что backend запущен.");
  }

  if (response.status === 401 && sentToken) {
    setToken(null);
    handleUnauthorized();
    return request<T>(method, path, body);
  }
  if (response.status === 204) return undefined as T;

  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, errorMessage(data, response.status));
  return data as T;
}
