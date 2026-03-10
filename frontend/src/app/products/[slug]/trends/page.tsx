"use client";

import { useEffect, useState } from "react";
import {
  getProducts,
  getProductTrends,
  getTopicSentiment,
  type TrendItem,
  type TopicSentiment,
} from "@/lib/api";
import { formatPct } from "@/lib/utils";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/utils";
import { Button } from "@/components/ui/button";

function SentimentBar({ value }: { value: number }) {
  const pct = Math.round(((value + 1) / 2) * 100);
  const color = value > 0.2 ? "var(--color-positive)" : value < -0.2 ? "var(--color-negative)" : "var(--color-ink-dim)";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[11px] font-mono w-12 text-right" style={{ color }}>
        {value > 0 ? "+" : ""}{value.toFixed(2)}
      </span>
    </div>
  );
}

function DrillDown({ productId, topic, slug }: { productId: number; topic: string; slug: string }) {
  const [data, setData] = useState<TopicSentiment | null>(null);

  useEffect(() => {
    getTopicSentiment(productId, topic).then(setData);
  }, [productId, topic]);

  if (!data) return <p className="text-xs text-muted-foreground py-3 px-4">Loading…</p>;

  return (
    <div className="px-4 py-3 space-y-3 bg-muted/20 border-t border-border">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {data.total_count} posts mentioning <span className="text-foreground font-medium">"{topic}"</span>
        </p>
        <a
          href={`/products/${slug}/feed?search=${encodeURIComponent(topic)}`}
          className="text-[11px] text-muted-foreground hover:text-foreground transition-colors underline underline-offset-2"
        >
          View in feed →
        </a>
      </div>

      <div className="space-y-1.5">
        <p className="text-[11px] text-muted-foreground">Overall sentiment</p>
        <SentimentBar value={data.avg_sentiment} />
      </div>

      {Object.keys(data.categories).length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[11px] text-muted-foreground">By category</p>
          {Object.entries(data.categories)
            .sort(([, a], [, b]) => b.count - a.count)
            .map(([cat, stats]) => (
              <div key={cat} className="grid grid-cols-[120px_1fr_80px] items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span
                    className="inline-block h-2 w-2 rounded-full shrink-0"
                    style={{ background: CATEGORY_COLORS[cat] ?? "#6B7280" }}
                  />
                  <span className="text-[11px] truncate">{CATEGORY_LABELS[cat] ?? cat.replace(/_/g, " ")}</span>
                </div>
                <SentimentBar value={stats.avg_sentiment} />
                <span className="text-[11px] font-mono text-muted-foreground text-right">{stats.count} posts</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

export default function TrendsPage({ params }: { params: { slug: string } }) {
  const [productId, setProductId] = useState<number | null>(null);
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [computedAt, setComputedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    getProducts().then((ps) => {
      const p = ps.find((x) => x.slug === params.slug);
      if (!p) return;
      setProductId(p.id);
      getProductTrends(p.id, 7, 50).then((res) => {
        setTrends(res.trends);
        setComputedAt(res.computed_at);
        setLoading(false);
      });
    });
  }, [params.slug]);

  function exportCsv() {
    const header = "topic,current_count,previous_count,pct_change,top_category\n";
    const rows = trends.map((t) => {
      const topCat =
        Object.entries(t.category_breakdown).sort(([, a], [, b]) => b - a)[0]?.[0] ?? "";
      return `"${t.topic}",${t.current_count},${t.previous_count},${t.pct_change.toFixed(1)},"${topCat}"`;
    });
    const csv = header + rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "trends.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <p className="p-8 text-muted-foreground">Loading…</p>;

  return (
    <main className="p-5 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Trending Topics</h1>
          {computedAt && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Computed {new Date(computedAt + "Z").toLocaleString()}
            </p>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={exportCsv} disabled={trends.length === 0}>
          Export CSV
        </Button>
      </div>

      {trends.length === 0 ? (
        <p className="text-muted-foreground text-sm">No trend data yet. Run a scout first.</p>
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">Topic</th>
                <th className="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground">Current</th>
                <th className="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground">Previous</th>
                <th className="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground">Change</th>
                <th className="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">Top Category</th>
              </tr>
            </thead>
            <tbody>
              {trends.map((t) => {
                const topCat =
                  Object.entries(t.category_breakdown).sort(([, a], [, b]) => b - a)[0]?.[0] ?? "—";
                const isExpanded = expanded === t.topic;
                return (
                  <>
                    <tr
                      key={t.topic}
                      className="border-t border-border cursor-pointer hover:bg-muted/30 transition-colors"
                      onClick={() => setExpanded(isExpanded ? null : t.topic)}
                    >
                      <td className="px-4 py-2.5 font-medium">
                        <span className="flex items-center gap-1.5">
                          <span className={`transition-transform text-muted-foreground text-[10px] ${isExpanded ? "rotate-90" : ""}`}>▶</span>
                          {t.topic}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums">{t.current_count}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">{t.previous_count}</td>
                      <td
                        className="px-4 py-2.5 text-right font-semibold tabular-nums"
                        style={{ color: t.pct_change >= 0 ? "var(--color-positive)" : "var(--color-negative)" }}
                      >
                        {formatPct(t.pct_change)}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="flex items-center gap-1.5">
                          <span className="h-2 w-2 rounded-full shrink-0" style={{ background: CATEGORY_COLORS[topCat] ?? "#6B7280" }} />
                          <span className="capitalize text-xs">{CATEGORY_LABELS[topCat] ?? topCat.replace(/_/g, " ")}</span>
                        </span>
                      </td>
                    </tr>
                    {isExpanded && productId && (
                      <tr key={`${t.topic}-drill`} className="border-t border-border">
                        <td colSpan={5} className="p-0">
                          <DrillDown productId={productId} topic={t.topic} slug={params.slug} />
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
