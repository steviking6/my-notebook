// Calls to the FastAPI backend, through our Next.js proxy (src/app/api/[...path]/route.ts).

const API_URL = "/api";

export type DocumentStatus = "uploaded" | "indexed" | "failed";

export type DocumentMeta = {
  id: string;
  filename: string;
  size_bytes: number;
  status: DocumentStatus;
  uploaded_at: string;
  chunk_count: number | null;
  error: string | null;
};

export type Chunk = {
  id: string;
  doc_id: string;
  filename: string;
  index: number;
  text: string;
  page: number | null;
  section: string | null;
};

export type AskResponse = {
  answer: string; // contains citations like [1], [2]
  sources: Chunk[]; // [n] in the answer = sources[n - 1]
  queries: string[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    // FastAPI puts the error message in "detail"
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : response.statusText;
    throw new Error(detail || `Error ${response.status}`);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export const listDocuments = () => request<DocumentMeta[]>("/documents");

export function uploadDocuments(files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  return request<DocumentMeta[]>("/documents", { method: "POST", body: form });
}

export const deleteDocument = (id: string) =>
  request<void>(`/documents/${id}`, { method: "DELETE" });

export const ingest = () => request<DocumentMeta[]>("/ingest", { method: "POST" });

export const ask = (question: string, level: number) =>
  request<AskResponse>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, level }),
  });
