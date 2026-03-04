"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
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

function StatusPip({ status }: { status: string | null }) {
  if (!status) return null;
  const color =
    status === "completed" ? "#3fb950" :
    status === "running"   ? "#f59e0b" :
                             "#f85149";
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-widest uppercase">
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      <span style={{ color }}>{status}</span>
    </span>
  );
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
    <div className="p-8">
      <p className="font-mono text-xs text-destructive tracking-wide">ERR: {error}</p>
    </div>
  );
  if (!product || !summary) return (
    <div className="p-8">
      <p className="font-mono text-xs text-muted-foreground tracking-widest animate-pulse">LOADING…</p>
    </div>
  );

  const sentimentColor =
    summary.avg_sentiment > 0.1  ? "#3fb950" :
    summary.avg_sentiment < -0.1 ? "#f85149" :
                                    "hsl(var(--muted-foreground))";

  return (
    <main className="p-6 max-w-6xl mx-auto space-y-6">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-start gap-4 pb-4 border-b border-border">
        <div className="flex-1 min-w-0 space-y-1">
          <h1 className="font-display font-bold text-xl tracking-tight text-foreground">
            {product.name}
          </h1>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-[11px] text-muted-foreground">
              Updated {formatRelativeTime(summary.last_scout_at)}
            </span>
            <StatusPip status={summary.last_scout_status} />
          </div>
        </div>
        <Button
          onClick={handleScout}
          disabled={scouting}
          size="sm"
          className="font-display font-semibold text-[11px] tracking-[0.12em] uppercase shrink-0"
        >
          {scouting ? "Scouting…" : "Run Scout"}
        </Button>
      </div>

      {/* ── Pulse bar ──────────────────────────────────────────────── */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="font-display text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground">
            Category Breakdown — Last 7 days
          </p>
          <p className="font-mono text-[11px] text-muted-foreground tabular-nums">
            {summary.total_items} items
          </p>
        </div>
        <PulseScoreBar
          counts={summary.category_counts}
          onCategoryClick={(cat) => handleCategorySelect(cat)}
        />
      </div>

      {/* ── Category cards ─────────────────────────────────────────── */}
      <CategoryCards
        counts={summary.category_counts}
        selectedCategory={selectedCategory}
        onSelect={handleCategorySelect}
      />

      {/* ── Sentiment strip ────────────────────────────────────────── */}
      <div className="flex items-center gap-4 py-3 px-4 bg-card border border-border rounded-sm">
        <p className="font-display text-[10px] font-semibold tracking-[0.18em] uppercase text-muted-foreground shrink-0">
          Avg Sentiment
        </p>
        <p
          className="font-mono text-xl font-medium tabular-nums"
          style={{ color: sentimentColor }}
        >
          {summary.avg_sentiment > 0 ? "+" : ""}{summary.avg_sentiment.toFixed(3)}
        </p>
        <Badge
          variant="outline"
          className="font-mono text-[10px] tracking-widest uppercase border-border"
        >
          {summary.sentiment_trend}
        </Badge>
        {summary.top_trend && (
          <div className="ml-auto flex items-center gap-2 min-w-0">
            <span className="font-display text-[10px] tracking-[0.15em] uppercase text-muted-foreground shrink-0">
              Top Trend
            </span>
            <span className="font-mono text-xs text-primary truncate">
              {summary.top_trend}
            </span>
          </div>
        )}
      </div>

      {/* ── Charts grid ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="border border-border rounded-sm p-4 space-y-3">
          <p className="font-display text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground">
            Trending Topics
          </p>
          <TrendingBarChart trends={trends?.trends ?? []} />
        </div>
        <div className="border border-border rounded-sm p-4 space-y-3">
          <p className="font-display text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground">
            Sentiment — Last 14 days
          </p>
          <SentimentTimeline feedbackItems={feedItems} />
        </div>
      </div>
    </main>
  );
}
