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

const GRID    = "#262420";
const TICK    = "#6b6560";
const BG_TIP  = "#141210";
const BDR_TIP = "#2a2620";

// Amber → brighter amber as pct_change increases
function getPctColor(pctChange: number): string {
  const clamped = Math.min(Math.max(pctChange, 0), 400);
  const ratio = clamped / 400;
  // dark muted amber → bright amber
  const r = Math.round(120 + (245 - 120) * ratio);
  const g = Math.round(80  + (158 - 80)  * ratio);
  const b = Math.round(20  + (11  - 20)  * ratio);
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
    <div style={{ background: BG_TIP, border: `1px solid ${BDR_TIP}`, padding: "10px 14px", borderRadius: 2 }}>
      <p style={{ fontFamily: "var(--font-syne)", fontSize: 11, fontWeight: 700, marginBottom: 6, letterSpacing: "0.05em" }}>
        {t.topic}
      </p>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: TICK }}>
        Current <span style={{ color: "#e8e2d8" }}>{t.current_count}</span>
        {" · "}Previous <span style={{ color: "#e8e2d8" }}>{t.previous_count}</span>
      </p>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#f59e0b", marginTop: 4 }}>
        {formatPct(t.pct_change)}
      </p>
      {Object.keys(t.category_breakdown).length > 0 && (
        <div style={{ marginTop: 6, borderTop: `1px solid ${BDR_TIP}`, paddingTop: 6 }}>
          {Object.entries(t.category_breakdown)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 3)
            .map(([cat, cnt]) => (
              <p key={cat} style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: TICK }}>
                {cat.replace(/_/g, " ")}: {cnt}
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
      <p className="py-8 text-center font-mono text-xs text-muted-foreground tracking-widest">
        NO TREND DATA — RUN A SCOUT
      </p>
    );
  }

  const data = [...trends]
    .sort((a, b) => b.pct_change - a.pct_change)
    .slice(0, 10)
    .reverse();

  return (
    <ResponsiveContainer width="100%" height={Math.max(280, data.length * 34)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="2 4" horizontal={false} stroke={GRID} />
        <XAxis
          type="number"
          tick={{ fontSize: 10, fill: TICK, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: GRID }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="topic"
          width={110}
          tick={{ fontSize: 10, fill: TICK, fontFamily: "var(--font-mono)" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="current_count" radius={[0, 2, 2, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={getPctColor(entry.pct_change)} />
          ))}
          <LabelList
            dataKey="pct_change"
            position="right"
            formatter={(v: unknown) => formatPct(Number(v))}
            style={{ fontSize: 10, fill: "#f59e0b", fontFamily: "var(--font-mono)" }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

interface TrendingBarChartProps {
  trends: TrendItem[];
}
