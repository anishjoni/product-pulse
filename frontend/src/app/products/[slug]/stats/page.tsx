"use client";

import { useEffect, useState, useCallback } from "react";
import { getProducts, getProductStats, type ProductStats } from "@/lib/api";

import { CategoryTimeline } from "@/components/pulse/CategoryTimeline";

const PERIODS = [
  { label: "7d", days: 7 },
  { label: "14d", days: 14 },
  { label: "30d", days: 30 },
];

const CATEGORIES = [
  "feature_request",
  "bug_report",
  "complaint",
  "praise",
  "general_discussion",
] as const;

export default function StatsPage({ params }: { params: { slug: string } }) {
  const [stats, setStats] = useState<ProductStats | null>(null);
  const [periodDays, setPeriodDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (days: number) => {
      try {
        const products = await getProducts();
        const p = products.find((x) => x.slug === params.slug);
        if (!p) { setError("Product not found."); return; }
        const s = await getProductStats(p.id, days);
        setStats(s);
      } catch (e) {
        setError((e as Error).message);
      }
    },
    [params.slug]
  );

  useEffect(() => { load(periodDays); }, [load, periodDays]);

  function handlePeriod(days: number) {
    setPeriodDays(days);
    setStats(null);
  }

  if (error) return (
    <p className="p-8 text-sm" style={{ color: "var(--color-negative)" }}>{error}</p>
  );

  // Compute category totals for the summary table
  const totals: Record<string, number> = {};
  if (stats) {
    for (const row of stats.data) {
      for (const cat of CATEGORIES) {
        totals[cat] = (totals[cat] ?? 0) + ((row[cat] as number) ?? 0);
      }
    }
  }
  const grandTotal = Object.values(totals).reduce((a, b) => a + b, 0);

  return (
    <main className="p-5 max-w-6xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Category breakdown</h1>
        <div className="flex items-center gap-1">
          {PERIODS.map(({ label, days }) => (
            <button
              key={days}
              onClick={() => handlePeriod(days)}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                periodDays === days
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Stacked area chart */}
      <div className="rounded bg-card border border-border p-4">
        <p className="text-xs text-muted-foreground mb-4">
          Daily category counts · last {periodDays} days
        </p>
        {!stats ? (
          <p className="py-12 text-center text-muted-foreground text-sm">Loading…</p>
        ) : (
          <CategoryTimeline data={stats.data} />
        )}
      </div>

      {/* Summary table */}
      {stats && grandTotal > 0 && (
        <div className="rounded bg-card border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Category</th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Total</th>
                <th className="px-4 py-2.5 text-right text-xs font-medium text-muted-foreground">Share</th>
              </tr>
            </thead>
            <tbody>
              {CATEGORIES.filter((cat) => (totals[cat] ?? 0) > 0)
                .sort((a, b) => (totals[b] ?? 0) - (totals[a] ?? 0))
                .map((cat) => (
                  <tr key={cat} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2.5 text-xs capitalize">{cat.replace(/_/g, " ")}</td>
                    <td className="px-4 py-2.5 text-xs text-right font-mono">{totals[cat]}</td>
                    <td className="px-4 py-2.5 text-xs text-right text-muted-foreground">
                      {grandTotal > 0 ? ((totals[cat] / grandTotal) * 100).toFixed(1) : "0"}%
                    </td>
                  </tr>
                ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-border bg-muted/20">
                <td className="px-4 py-2.5 text-xs font-medium">Total</td>
                <td className="px-4 py-2.5 text-xs text-right font-mono font-medium">{grandTotal}</td>
                <td className="px-4 py-2.5 text-xs text-right text-muted-foreground">100%</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </main>
  );
}
