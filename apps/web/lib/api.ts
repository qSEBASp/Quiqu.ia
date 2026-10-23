export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join(". ");
    }
    return `Error ${response.status}`;
  } catch {
    return `Error ${response.status}`;
  }
}

export async function getJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<T>;
}

async function send<T>(
  method: "POST" | "PUT",
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<T>;
}

export function postJSON<T>(path: string, body?: unknown): Promise<T> {
  return send<T>("POST", path, body);
}

export function putJSON<T>(path: string, body: unknown): Promise<T> {
  return send<T>("PUT", path, body);
}
