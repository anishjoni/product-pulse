"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from "recharts";
import type { TrendItem } from "@/lib/api";
import { formatPct } from "@/lib/utils";

interface TrendingBarChartProps {
  trends: TrendItem[];
}

function getPctColor(pctChange: number): string {
  // Gradient from gray (#6B7280) to blue (#3B82F6) based on intensity
  const clamped = Math.min(Math.max(pctChange, 0), 500);
  const ratio = clamped / 500;
  // Interpolate between gray and blue
  const r = Math.round(107 + (59 - 107) * ratio);
  const g = Math.round(114 + (130 - 114) * ratio);
  const b = Math.round(128 + (246 - 128) * ratio);
  return `rgb(${r},${g},${b})`;
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: TrendItem }[];
}) => {
  if (!active || !payload?.length) return null;
  const t = payload[0].payload;
  return (
    <div className="rounded-lg border bg-background p-3 shadow-lg text-sm">
      <p className="font-semibold mb-1">{t.topic}</p>
      <p>Current: {t.current_count}</p>
      <p>Previous: {t.previous_count}</p>
      <p>Change: {formatPct(t.pct_change)}</p>
      {Object.keys(t.category_breakdown).length > 0 && (
        <div className="mt-2">
          <p className="text-muted-foreground">Top categories:</p>
          {Object.entries(t.category_breakdown)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 3)
            .map(([cat, cnt]) => (
              <p key={cat}>
                {cat}: {cnt}
              </p>
            ))}
        </div>
      )}
    </div>
  );
};

export function TrendingBarChart({ trends }: TrendingBarChartProps) {
  if (trends.length === 0) {
    return (
      <p className="py-8 text-center text-muted-foreground text-sm">
        No trend data yet. Run a scout to generate trends.
      </p>
    );
  }

  const data = [...trends]
    .sort((a, b) => b.pct_change - a.pct_change)
    .slice(0, 10)
    .reverse(); // reverse so largest is at top

  return (
    <ResponsiveContainer width="100%" height={Math.max(300, data.length * 36)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 60, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} />
        <YAxis
          type="category"
          dataKey="topic"
          width={120}
          tick={{ fontSize: 11 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="current_count" radius={[0, 4, 4, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={getPctColor(entry.pct_change)} />
          ))}
          <LabelList
            dataKey="pct_change"
            position="right"
            formatter={(v: unknown) => formatPct(Number(v))}
            style={{ fontSize: 11, fill: "#6B7280" }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
