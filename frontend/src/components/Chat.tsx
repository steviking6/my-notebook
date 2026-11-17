"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { AskResponse, Chunk, ask } from "@/lib/api";
import { LEVELS } from "@/lib/levels";

type Message =
  | { role: "user"; text: string }
  | { role: "assistant"; response: AskResponse; level: number; seconds: number };

type Props = { hasIndexedSources: boolean; onError: (message: string) => void };

export default function Chat({ hasIndexedSources, onError }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [level, setLevel] = useState(3);
  const [loading, setLoading] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  // Braces matter: an effect may only return a clean-up function, and recent
  // browsers make scrollIntoView return a Promise.
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (!text || loading) return;
    setQuestion("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    const start = performance.now();
    try {
      const response = await ask(text, level);
      const seconds = (performance.now() - start) / 1000;
      setMessages((m) => [...m, { role: "assistant", response, level, seconds }]);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="flex h-full flex-col bg-zinc-50 dark:bg-zinc-950">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && <EmptyState hasIndexedSources={hasIndexedSources} />}
          {messages.map((message, i) =>
            message.role === "user" ? (
              <div key={i} className="flex justify-end">
                <p className="max-w-[80%] rounded-2xl bg-indigo-600 px-4 py-2 text-white">{message.text}</p>
              </div>
            ) : (
              <AssistantMessage key={i} {...message} />
            ),
          )}
          {loading && (
            <p className="animate-pulse text-sm text-zinc-500">
              Searching your notes ({LEVELS[level].name}, {LEVELS[level].queries} queries)…
            </p>
          )}
          <div ref={bottom} />
        </div>
      </div>

      <form onSubmit={submit} className="border-t border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto max-w-3xl space-y-3">
          <EfficiencySlider level={level} onChange={setLevel} />
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={hasIndexedSources ? "Ask a question about your notes…" : "Index a source first…"}
              className="flex-1 rounded-xl border border-zinc-300 bg-white px-4 py-2.5 text-zinc-900 outline-none focus:border-indigo-500 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="rounded-xl bg-indigo-600 px-5 font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-zinc-300 dark:disabled:bg-zinc-700"
            >
              Ask
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}

function EmptyState({ hasIndexedSources }: { hasIndexedSources: boolean }) {
  return (
    <div className="mt-20 text-center">
      <h1 className="text-2xl font-semibold text-zinc-800 dark:text-zinc-100">Ask your course notes</h1>
      <p className="mt-2 text-zinc-500">
        {hasIndexedSources
          ? "Answers only use your sources, with citations you can check."
          : "1. Add sources on the left  ·  2. Click “Chunk & Index”  ·  3. Ask a question"}
      </p>
    </div>
  );
}

function EfficiencySlider({ level, onChange }: { level: number; onChange: (level: number) => void }) {
  const info = LEVELS[level];
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
      <label htmlFor="level" className="font-medium text-zinc-700 dark:text-zinc-200">
        Efficiency
      </label>
      <input
        id="level"
        type="range"
        min={1}
        max={5}
        value={level}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-40 accent-indigo-600"
      />
      <span className="font-medium text-indigo-600 dark:text-indigo-400">
        {level} · {info.name}
      </span>
      <span className="text-xs text-zinc-500">
        {info.queries} {info.queries > 1 ? "queries" : "query"} · {info.chunks} chunks · {info.reranker} rerank ·{" "}
        {info.latency} · {info.cost}
      </span>
    </div>
  );
}

function AssistantMessage({ response, level, seconds }: { response: AskResponse; level: number; seconds: number }) {
  const [open, setOpen] = useState<number | null>(null); // source number shown in full
  const cited = citedNumbers(response.answer, response.sources.length);

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="whitespace-pre-wrap leading-relaxed text-zinc-800 dark:text-zinc-100">
        {renderWithCitations(response.answer, response.sources.length, setOpen)}
      </div>

      {cited.length > 0 && (
        <div className="mt-4 border-t border-zinc-100 pt-3 dark:border-zinc-800">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">Sources</p>
          <ul className="space-y-1">
            {cited.map((n) => (
              <SourceItem
                key={n}
                n={n}
                chunk={response.sources[n - 1]}
                open={open === n}
                toggle={() => setOpen(open === n ? null : n)}
              />
            ))}
          </ul>
        </div>
      )}

      <p className="mt-3 text-xs text-zinc-400">
        Level {level} · {seconds.toFixed(1)} s · {response.queries.length} queries
      </p>
    </div>
  );
}

function SourceItem({ n, chunk, open, toggle }: { n: number; chunk: Chunk; open: boolean; toggle: () => void }) {
  const where = [chunk.filename, chunk.page ? `p. ${chunk.page}` : null, chunk.section].filter(Boolean).join(" · ");
  return (
    <li>
      <button onClick={toggle} className="flex w-full items-start gap-2 text-left text-sm hover:text-indigo-600">
        <Badge n={n} />
        <span className="text-zinc-600 dark:text-zinc-300">{where}</span>
      </button>
      {open && (
        <p className="ml-7 mt-1 whitespace-pre-wrap rounded-lg bg-zinc-50 p-3 text-sm text-zinc-700 dark:bg-zinc-950 dark:text-zinc-300">
          {chunk.text}
        </p>
      )}
    </li>
  );
}

function Badge({ n }: { n: number }) {
  return (
    <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-indigo-100 px-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-900 dark:text-indigo-200">
      {n}
    </span>
  );
}

// "... the noise [2][3]." -> text with clickable [2] and [3] badges
function renderWithCitations(answer: string, nSources: number, onClick: (n: number) => void) {
  return answer.split(/(\[\d+\])/g).map((part, i) => {
    const n = Number(part.match(/^\[(\d+)\]$/)?.[1]);
    if (!n || n > nSources) return part;
    return (
      <button key={i} onClick={() => onClick(n)} className="mx-0.5 align-baseline">
        <Badge n={n} />
      </button>
    );
  });
}

function citedNumbers(answer: string, nSources: number): number[] {
  const numbers = [...answer.matchAll(/\[(\d+)\]/g)].map((m) => Number(m[1]));
  return [...new Set(numbers)].filter((n) => n >= 1 && n <= nSources).sort((a, b) => a - b);
}
