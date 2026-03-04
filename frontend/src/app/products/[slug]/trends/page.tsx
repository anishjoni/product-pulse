"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getProducts,
  getProductTrends,
  type TrendItem,
} from "@/lib/api";
import { formatPct } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { CATEGORY_LABELS } from "@/lib/utils";

export default function TrendsPage({ params }: { params: { slug: string } }) {
  const router = useRouter();
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [computedAt, setComputedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProducts().then((ps) => {
      const p = ps.find((x) => x.slug === params.slug);
      if (!p) return;
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

  if (loading) return (
    <p className="p-8 font-mono text-[10px] tracking-widest uppercase text-muted-foreground animate-pulse">
      LOADING…
    </p>
  );

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-5">
      <div className="flex items-start justify-between pb-4 border-b border-border">
        <div className="space-y-1">
          <h1 className="font-display font-bold text-xl tracking-tight text-foreground">
            Trending Topics
          </h1>
          {computedAt && (
            <p className="font-mono text-[10px] text-muted-foreground tracking-widest">
              COMPUTED {new Date(computedAt + "Z").toLocaleString().toUpperCase()}
            </p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={exportCsv}
          disabled={trends.length === 0}
          className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground hover:text-foreground h-7 px-3 border border-border"
        >
          EXPORT CSV ↓
        </Button>
      </div>

      {trends.length === 0 ? (
        <p className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground py-8 text-center">
          NO TREND DATA — RUN A SCOUT
        </p>
      ) : (
        <div className="border border-border rounded-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-card">
                <th className="text-left px-4 py-2 font-display text-[10px] tracking-[0.18em] uppercase text-muted-foreground font-semibold">Topic</th>
                <th className="text-right px-4 py-2 font-display text-[10px] tracking-[0.18em] uppercase text-muted-foreground font-semibold">Current</th>
                <th className="text-right px-4 py-2 font-display text-[10px] tracking-[0.18em] uppercase text-muted-foreground font-semibold">Previous</th>
                <th className="text-right px-4 py-2 font-display text-[10px] tracking-[0.18em] uppercase text-muted-foreground font-semibold">Change</th>
                <th className="text-left px-4 py-2 font-display text-[10px] tracking-[0.18em] uppercase text-muted-foreground font-semibold">Category</th>
              </tr>
            </thead>
            <tbody>
              {trends.map((t, i) => {
                const topCat =
                  Object.entries(t.category_breakdown).sort(([, a], [, b]) => b - a)[0]?.[0] ?? "—";
                const pctColor = t.pct_change >= 0 ? "#3fb950" : "#f85149";
                return (
                  <tr
                    key={i}
                    tabIndex={0}
                    className="border-t border-border cursor-pointer hover:bg-card transition-colors focus-visible:outline-none focus-visible:bg-card"
                    onClick={() =>
                      router.push(
                        `/products/${params.slug}/feed?search=${encodeURIComponent(t.topic)}`
                      )
                    }
                    onKeyDown={(e) =>
                      (e.key === "Enter" || e.key === " ") &&
                      router.push(
                        `/products/${params.slug}/feed?search=${encodeURIComponent(t.topic)}`
                      )
                    }
                  >
                    <td className="px-4 py-2.5 font-mono text-xs text-foreground/90">{t.topic}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-right tabular-nums text-muted-foreground">{t.current_count}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-right tabular-nums text-muted-foreground">{t.previous_count}</td>
                    <td
                      className="px-4 py-2.5 font-mono text-xs text-right tabular-nums font-medium"
                      style={{ color: pctColor }}
                    >
                      {formatPct(t.pct_change)}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[10px] tracking-widest uppercase text-muted-foreground">
                      {CATEGORY_LABELS[topCat] ?? topCat.replace(/_/g, " ")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
