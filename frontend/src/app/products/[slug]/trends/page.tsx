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

  if (loading) return <p className="p-8 text-muted-foreground">Loading…</p>;

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Trending Topics</h1>
          {computedAt && (
            <p className="text-sm text-muted-foreground">
              Computed at {new Date(computedAt + "Z").toLocaleString()}
            </p>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={exportCsv} disabled={trends.length === 0}>
          Export CSV
        </Button>
      </div>

      {trends.length === 0 ? (
        <p className="text-muted-foreground">No trend data yet. Run a scout first.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Topic</th>
                <th className="text-right px-4 py-2 font-medium">Current</th>
                <th className="text-right px-4 py-2 font-medium">Previous</th>
                <th className="text-right px-4 py-2 font-medium">Change</th>
                <th className="text-left px-4 py-2 font-medium">Top Category</th>
              </tr>
            </thead>
            <tbody>
              {trends.map((t, i) => {
                const topCat =
                  Object.entries(t.category_breakdown).sort(([, a], [, b]) => b - a)[0]?.[0] ?? "—";
                return (
                  <tr
                    key={i}
                    className="border-t cursor-pointer hover:bg-muted/30 transition-colors"
                    onClick={() =>
                      router.push(
                        `/products/${params.slug}/feed?search=${encodeURIComponent(t.topic)}`
                      )
                    }
                  >
                    <td className="px-4 py-2 font-medium">{t.topic}</td>
                    <td className="px-4 py-2 text-right">{t.current_count}</td>
                    <td className="px-4 py-2 text-right">{t.previous_count}</td>
                    <td
                      className="px-4 py-2 text-right font-semibold tabular-nums"
                      style={{ color: t.pct_change >= 0 ? "var(--color-positive)" : "var(--color-negative)" }}
                    >
                      {formatPct(t.pct_change)}
                    </td>
                    <td className="px-4 py-2 capitalize">{topCat.replace(/_/g, " ")}</td>
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
