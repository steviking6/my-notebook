// Efficiency levels: same values as backend/app/services/retrieval.py (LEVELS).
// Latency and cost are rough estimates, shown so the student understands the trade-off.

export type LevelInfo = {
  name: string;
  queries: number;
  chunks: number;
  reranker: string;
  latency: string;
  cost: string;
};

export const LEVELS: Record<number, LevelInfo> = {
  1: { name: "Fast", queries: 1, chunks: 4, reranker: "FlashRank", latency: "~2 s", cost: "< $0.001" },
  2: { name: "Light", queries: 3, chunks: 5, reranker: "FlashRank", latency: "~3 s", cost: "~$0.001" },
  3: { name: "Balanced", queries: 4, chunks: 6, reranker: "FlashRank", latency: "~4 s", cost: "~$0.002" },
  4: { name: "Deep", queries: 6, chunks: 8, reranker: "FlashRank", latency: "~5 s", cost: "~$0.003" },
  5: { name: "Exhaustive", queries: 8, chunks: 10, reranker: "LLM", latency: "~10 s", cost: "~$0.01" },
};
