"use client";

import { useCallback, useEffect, useState } from "react";
import Chat from "@/components/Chat";
import SourcesPanel from "@/components/SourcesPanel";
import { DocumentMeta, listDocuments } from "@/lib/api";

export default function Home() {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await listDocuments());
    } catch {
      setError("Cannot reach the API. Is the backend running on port 8000?");
    }
  }, []);

  // Load the documents once, when the page opens.
  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch(() => setError("Cannot reach the API. Is the backend running on port 8000?"));
  }, []);

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-2 border-b border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
        <span className="text-lg">📓</span>
        <span className="font-semibold text-zinc-900 dark:text-zinc-100">My Notebook</span>
      </header>

      {error && (
        <div className="flex items-center justify-between bg-red-50 px-4 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          <span>{error}</span>
          <button onClick={() => setError(null)} aria-label="Close">
            ✕
          </button>
        </div>
      )}

      <main className="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[300px_1fr]">
        <SourcesPanel documents={documents} onChange={setDocuments} refresh={refresh} onError={setError} />
        <Chat hasIndexedSources={documents.some((d) => d.status === "indexed")} onError={setError} />
      </main>
    </div>
  );
}
