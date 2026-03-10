"use client";

import { useState } from "react";
import Link from "next/link";
import { compareTopicAcrossProducts, type TopicCompareItem } from "@/lib/api";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/utils";
import { Button } from "@/components/ui/button";

function SentimentBadge({ value }: { value: number }) {
  const label = value > 0.2 ? "Positive" : value < -0.2 ? "Negative" : "Neutral";
  const color = value > 0.2 ? "var(--color-positive)" : value < -0.2 ? "var(--color-negative)" : "var(--color-ink-dim)";
  return (
    <span className="text-[11px] font-medium" style={{ color }}>
      {value > 0 ? "+" : ""}{value.toFixed(2)} {label}
    </span>
  );
}

function CategoryBar({ breakdown, total }: { breakdown: Record<string, number>; total: number }) {
  if (total === 0) return null;
  const categories = Object.entries(breakdown).sort(([, a], [, b]) => b - a);
  return (
    <div className="flex h-2 rounded-full overflow-hidden w-full">
      {categories.map(([cat, cnt]) => (
        <div
          key={cat}
          title={`${CATEGORY_LABELS[cat] ?? cat}: ${cnt}`}
          style={{
            width: `${(cnt / total) * 100}%`,
            background: CATEGORY_COLORS[cat] ?? "#6B7280",
          }}
        />
      ))}
    </div>
  );
}

function ResultCard({ item }: { item: TopicCompareItem }) {
  const topCat = item.top_category;
  return (
    <div className="rounded bg-card border border-border p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{item.product_name}</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {item.total_count} matching posts
          </p>
        </div>
        <div className="text-right shrink-0">
          <SentimentBadge value={item.avg_sentiment} />
          {topCat && (
            <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center justify-end gap-1">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: CATEGORY_COLORS[topCat] ?? "#6B7280" }} />
              {CATEGORY_LABELS[topCat] ?? topCat.replace(/_/g, " ")}
            </p>
          )}
        </div>
      </div>
      <CategoryBar breakdown={item.category_breakdown} total={item.total_count} />
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {Object.entries(item.category_breakdown)
          .sort(([, a], [, b]) => b - a)
          .map(([cat, cnt]) => (
            <span key={cat} className="text-[11px] text-muted-foreground flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: CATEGORY_COLORS[cat] ?? "#6B7280" }} />
              {CATEGORY_LABELS[cat] ?? cat.replace(/_/g, " ")} {cnt}
            </span>
          ))}
      </div>
    </div>
  );
}

export default function ComparePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<TopicCompareItem[] | null>(null);
  const [searchedTopic, setSearchedTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch() {
    if (query.trim().length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const res = await compareTopicAcrossProducts(query.trim());
      setResults(res.results);
      setSearchedTopic(res.topic);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-5 max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-1.5 shrink-0">
          <span className="h-2 w-2 rounded-full bg-primary" />
          <span className="text-sm font-semibold tracking-tight">Pulse</span>
        </Link>
        <span className="text-border select-none">/</span>
        <span className="text-sm text-muted-foreground">Compare topic across products</span>
      </div>

      {/* Search */}
      <div className="space-y-2">
        <p className="text-xs text-muted-foreground">
          Search for a topic or keyword to see how it appears across all your tracked products.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="e.g. options spreads, dark mode, crash..."
            className="flex-1 rounded border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Button onClick={handleSearch} disabled={loading || query.trim().length < 2} size="sm">
            {loading ? "Searching…" : "Compare"}
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && <p className="text-sm" style={{ color: "var(--color-negative)" }}>{error}</p>}

      {/* Results */}
      {results !== null && (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground">
            {results.length === 0
              ? `No posts found mentioning "${searchedTopic}".`
              : `"${searchedTopic}" mentioned across ${results.length} product${results.length > 1 ? "s" : ""}`}
          </p>
          {results.map((item) => (
            <ResultCard key={item.product_id} item={item} />
          ))}
        </div>
      )}
    </main>
  );
}
