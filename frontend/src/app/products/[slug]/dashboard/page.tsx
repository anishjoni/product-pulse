"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
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

function statusBadge(status: string | null) {
  if (!status) return null;
  const variant =
    status === "completed"
      ? "bg-green-100 text-green-800"
      : status === "running"
      ? "bg-yellow-100 text-yellow-800"
      : "bg-red-100 text-red-800";
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${variant}`}>
      {status}
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

  if (error) return <p className="p-8 text-red-500">{error}</p>;
  if (!product || !summary) return <p className="p-8 text-muted-foreground">Loading…</p>;

  return (
    <main className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header strip */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{product.name}</h1>
          <p className="text-sm text-muted-foreground">
            Last updated {formatRelativeTime(summary.last_scout_at)}
            {summary.last_scout_status && (
              <> &nbsp;{statusBadge(summary.last_scout_status)}</>
            )}
          </p>
        </div>
        <Button onClick={handleScout} disabled={scouting} size="sm">
          {scouting ? "Scouting…" : "Run Scout Now"}
        </Button>
      </div>

      <Separator />

      {/* Pulse Score Bar */}
      <div className="space-y-1">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
          Category Breakdown — Last 7 days ({summary.total_items} items)
        </h2>
        <PulseScoreBar
          counts={summary.category_counts}
          onCategoryClick={(cat) => handleCategorySelect(cat)}
        />
      </div>

      {/* Category Cards */}
      <CategoryCards
        counts={summary.category_counts}
        selectedCategory={selectedCategory}
        onSelect={handleCategorySelect}
      />

      {/* Avg sentiment */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">Avg sentiment:</span>
        <span
          className="font-semibold"
          style={{
            color:
              summary.avg_sentiment > 0.1
                ? "#22C55E"
                : summary.avg_sentiment < -0.1
                ? "#EF4444"
                : "#6B7280",
          }}
        >
          {summary.avg_sentiment.toFixed(3)}
        </span>
        <Badge variant="outline" className="text-xs">
          {summary.sentiment_trend}
        </Badge>
        {summary.top_trend && (
          <span className="ml-4 text-muted-foreground">
            Top trend: <span className="font-medium text-foreground">{summary.top_trend}</span>
          </span>
        )}
      </div>

      <Separator />

      {/* Charts grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Trending Topics
          </h2>
          <TrendingBarChart trends={trends?.trends ?? []} />
        </div>
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Sentiment — Last 14 days
          </h2>
          <SentimentTimeline feedbackItems={feedItems} />
        </div>
      </div>
    </main>
  );
}
