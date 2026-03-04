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
import { useTheme } from "@/contexts/theme";

// Coolors palette: #264653-2a9d8f-e9c46a-f4a261-e76f51
// Maps from least trending (cool teal) → most trending (burnt coral)
const PALETTE = ["#264653", "#2A9D8F", "#E9C46A", "#F4A261", "#E76F51"];

function paletteColor(index: number, total: number): string {
  const pos = total <= 1 ? 1 : index / (total - 1);
  return PALETTE[Math.round(pos * (PALETTE.length - 1))];
}

interface TrendingBarChartProps {
  trends: TrendItem[];
}

export function TrendingBarChart({ trends }: TrendingBarChartProps) {
  const { isDark } = useTheme();

  const C = isDark
    ? { grid: "#21262D", tick: "#484F58", tooltipBg: "#1C2333", tooltipBorder: "#30363D", tooltipText: "#E6EDF3", label: "#8B949E" }
    : { grid: "#E5E7EB", tick: "#9CA3AF", tooltipBg: "#FFFFFF",  tooltipBorder: "#E5E7EB",  tooltipText: "#111827",  label: "#9CA3AF" };

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
    .reverse(); // lowest at index 0 (bottom), highest at last (top)

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
      <div
        className="rounded px-3 py-2 text-xs space-y-0.5"
        style={{ background: C.tooltipBg, border: `1px solid ${C.tooltipBorder}`, color: C.tooltipText }}
      >
        <p className="font-semibold mb-1">{t.topic}</p>
        <p>Current: <span className="font-mono">{t.current_count}</span></p>
        <p>Previous: <span className="font-mono">{t.previous_count}</span></p>
        <p>Change: <span className="font-mono">{formatPct(t.pct_change)}</span></p>
        {Object.keys(t.category_breakdown).length > 0 && (
          <div className="mt-1.5 pt-1.5 border-t" style={{ borderColor: C.tooltipBorder }}>
            {Object.entries(t.category_breakdown)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 3)
              .map(([cat, cnt]) => (
                <p key={cat} style={{ color: C.label }}>
                  {cat.replace(/_/g, " ")}: {cnt}
                </p>
              ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={Math.max(280, data.length * 32)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 52, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={true} horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 10, fill: C.tick }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="topic" width={112} tick={{ fontSize: 10, fill: C.tick }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(99,102,241,0.05)" }} />
        <Bar dataKey="current_count" radius={[0, 3, 3, 0]}>
          {data.map((_, index) => (
            <Cell key={index} fill={paletteColor(index, data.length)} />
          ))}
          <LabelList
            dataKey="pct_change"
            position="right"
            formatter={(v: unknown) => formatPct(Number(v))}
            style={{ fontSize: 10, fill: C.label }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
