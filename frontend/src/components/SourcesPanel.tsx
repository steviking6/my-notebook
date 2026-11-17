"use client";

import { useRef, useState } from "react";
import { DocumentMeta, deleteDocument, ingest, uploadDocuments } from "@/lib/api";

type Props = {
  documents: DocumentMeta[];
  onChange: (documents: DocumentMeta[]) => void;
  refresh: () => Promise<void>;
  onError: (message: string) => void;
};

const ACCEPT = ".pdf,.html,.htm,.txt,.md,.sql,.csv,.docx,.pptx";

export default function SourcesPanel({ documents, onChange, refresh, onError }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState<"upload" | "ingest" | null>(null);
  const toIndex = documents.filter((d) => d.status !== "indexed").length;

  async function run(kind: "upload" | "ingest", action: () => Promise<unknown>) {
    setBusy(kind);
    try {
      await action();
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setBusy(null);
    }
  }

  function upload(files: FileList | null) {
    if (!files?.length) return;
    run("upload", async () => {
      await uploadDocuments(Array.from(files));
      await refresh();
    });
    if (input.current) input.current.value = ""; // allow re-uploading the same file
  }

  function remove(id: string) {
    run("upload", async () => {
      await deleteDocument(id);
      await refresh();
    });
  }

  return (
    <aside className="flex h-full flex-col gap-4 border-r border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">Sources</h2>
        <span className="text-xs text-zinc-400">{documents.length} file(s)</span>
      </div>

      <button
        onClick={() => input.current?.click()}
        disabled={busy !== null}
        className="rounded-lg border border-dashed border-zinc-300 px-3 py-4 text-sm text-zinc-600 transition hover:border-indigo-400 hover:text-indigo-600 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300"
      >
        {busy === "upload" ? "Uploading…" : "+ Add sources"}
        <span className="mt-1 block text-xs text-zinc-400">PDF, DOCX, PPTX, HTML, MD, TXT, SQL, CSV</span>
      </button>
      <input
        ref={input}
        type="file"
        multiple
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => upload(e.target.files)}
      />

      <ul className="flex-1 space-y-2 overflow-y-auto">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="group rounded-lg border border-zinc-200 px-3 py-2 dark:border-zinc-800"
            title={doc.error ?? undefined}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="break-all text-sm text-zinc-800 dark:text-zinc-100">{doc.filename}</span>
              <button
                onClick={() => remove(doc.id)}
                disabled={busy !== null}
                className="text-zinc-400 opacity-0 transition hover:text-red-500 group-hover:opacity-100"
                aria-label={`Delete ${doc.filename}`}
              >
                ✕
              </button>
            </div>
            <StatusBadge doc={doc} />
          </li>
        ))}
        {documents.length === 0 && (
          <li className="px-1 text-sm text-zinc-400">No sources yet. Add your course notes to start.</li>
        )}
      </ul>

      <button
        onClick={() => run("ingest", async () => onChange(await ingest()))}
        disabled={busy !== null || toIndex === 0}
        className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-zinc-300 dark:disabled:bg-zinc-700"
      >
        {busy === "ingest" ? "Chunking & indexing…" : `Chunk & Index${toIndex ? ` (${toIndex})` : ""}`}
      </button>
    </aside>
  );
}

function StatusBadge({ doc }: { doc: DocumentMeta }) {
  const styles = {
    uploaded: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
    indexed: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
    failed: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
  };
  const label = {
    uploaded: "Not indexed",
    indexed: `Indexed · ${doc.chunk_count} chunks`,
    failed: "Failed",
  };
  return (
    <span className={`mt-1 inline-block rounded px-1.5 py-0.5 text-xs ${styles[doc.status]}`}>
      {label[doc.status]}
    </span>
  );
}
