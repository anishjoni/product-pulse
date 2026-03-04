"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PulseScoreBar } from "@/components/pulse/PulseScoreBar";
import { CategoryCards } from "@/components/pulse/CategoryCards";
import { TrendingBarChart } from "@/components/pulse/TrendingBarChart";
import { SentimentTimeline } from "@/components/pulse/SentimentTimeline";
import {
  getProducts,
  getProductSummary,
  getProductTrends,
  getProductFeedback,
  triggerScout,
  type ProductSummary,
  type TrendsResponse,
  type FeedbackItem,
  type Product,
} from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

function scoutStatusChip(status: string | null) {
  if (!status) return null;
  const styles =
    status === "completed"
      ? "bg-[#10B981]/15 text-[#10B981]"
      : status === "running"
      ? "bg-[#F59E0B]/15 text-[#F59E0B]"
      : "bg-[#EF4444]/15 text-[#EF4444]";
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${styles}`}>
      {status}
    </span>
  );
}

function sentimentDisplay(avg: number): { label: string; color: string } {
  if (avg > 0.3) return { label: "Positive", color: "var(--color-positive)" };
  if (avg > 0.05) return { label: "Slightly positive", color: "var(--color-positive)" };
  if (avg < -0.3) return { label: "Negative", color: "var(--color-negative)" };
  if (avg < -0.05) return { label: "Slightly negative", color: "var(--color-negative)" };
  return { label: "Neutral", color: "var(--color-ink-dim)" };
}

export default function DashboardPage({ params }: { params: { slug: string } }) {
  const router = useRouter();
  const [product, setProduct] = useState<Product | null>(null);
  const [summary, setSummary] = useState<ProductSummary | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [feedItems, setFeedItems] = useState<FeedbackItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [scouting, setScouting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const products = await getProducts();
      const p = products.find((x) => x.slug === params.slug);
      if (!p) { setError("Product not found."); return; }
      setProduct(p);

      const [sum, tr, feed] = await Promise.all([
        getProductSummary(p.id),
        getProductTrends(p.id, 7, 10),
        getProductFeedback(p.id, { page_size: 100 }),
      ]);
      setSummary(sum);
      setTrends(tr);
      setFeedItems(feed.items);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [params.slug]);

  useEffect(() => { load(); }, [load]);

  async function handleScout() {
    if (!product || scouting) return;
    setScouting(true);
    try {
      await triggerScout(product.id);
      await load();
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setScouting(false);
    }
  }

  function handleCategorySelect(cat: string | null) {
    setSelectedCategory(cat);
    if (cat) router.push(`/products/${params.slug}/feed?category=${cat}`);
  }

  if (error) return (
    <p className="p-8 text-sm" style={{ color: "var(--color-negative)" }}>{error}</p>
  );
  if (!product || !summary) return (
    <p className="p-8 text-sm text-muted-foreground">Loading…</p>
  );

  const sentiment = sentimentDisplay(summary.avg_sentiment);

  return (
    <main className="p-5 max-w-6xl mx-auto space-y-5">

      {/* Header */}
      <div className="flex items-center gap-4 min-w-0">
        <div className="min-w-0 flex-1">
          <h1 className="text-lg font-semibold truncate">{product.name}</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-muted-foreground">
              Updated {formatRelativeTime(summary.last_scout_at)}
            </span>
            {scoutStatusChip(summary.last_scout_status)}
            {summary.top_trend && (
              <span className="text-xs text-muted-foreground">
                · top trend:{" "}
                <span className="text-foreground">{summary.top_trend}</span>
              </span>
            )}
          </div>
        </div>
        <Button
          onClick={handleScout}
          disabled={scouting}
          size="sm"
          className="shrink-0"
        >
          {scouting ? "Scouting…" : "Run Scout"}
        </Button>
      </div>

      {/* Vitals strip — the hero */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground">
            {summary.total_items} items · last 7 days
          </span>
          <span className="text-xs" style={{ color: sentiment.color }}>
            {sentiment.label}{" "}
            {summary.sentiment_trend === "improving" ? "↑" :
             summary.sentiment_trend === "declining" ? "↓" : "→"}
          </span>
        </div>
        <PulseScoreBar
          counts={summary.category_counts}
          selectedCategory={selectedCategory}
          onCategoryClick={handleCategorySelect}
        />
      </div>

      {/* Category cards */}
      <CategoryCards
        counts={summary.category_counts}
        selectedCategory={selectedCategory}
        onSelect={handleCategorySelect}
      />

      {/* Charts */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 pt-1">
        <div className="rounded bg-card border border-border p-4">
          <p className="text-xs text-muted-foreground mb-3">Trending topics</p>
          <TrendingBarChart trends={trends?.trends ?? []} />
        </div>
        <div className="rounded bg-card border border-border p-4">
          <p className="text-xs text-muted-foreground mb-3">Sentiment · 14 days</p>
          <SentimentTimeline feedbackItems={feedItems} />
        </div>
      </div>
    </main>
  );
}
