"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useTheme } from "@/contexts/theme";
import { ALL_CATEGORIES, CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/utils";

interface CategoryTimelineProps {
  data: Record<string, number | string>[];
}

export function CategoryTimeline({ data }: CategoryTimelineProps) {
  const { isDark } = useTheme();

  const C = isDark
    ? { grid: "#21262D", tick: "#484F58", tooltipBg: "#1C2333", tooltipBorder: "#30363D", tooltipText: "#E6EDF3" }
    : { grid: "#E5E7EB", tick: "#9CA3AF", tooltipBg: "#FFFFFF",  tooltipBorder: "#E5E7EB",  tooltipText: "#111827" };

  if (data.length === 0) {
    return (
      <p className="py-12 text-center text-muted-foreground text-sm">
        No data yet. Run a scout to generate stats.
      </p>
    );
  }

  // Format date label: "Mar 01"
  function fmtDate(d: string): string {
    const dt = new Date(d + "T00:00:00");
    return dt.toLocaleDateString("en-US", { month: "short", day: "2-digit" });
  }

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: { name: string; value: number; color: string }[];
    label?: string;
  }) => {
    if (!active || !payload?.length) return null;
    return (
      <div
        className="rounded px-3 py-2 text-xs space-y-0.5"
        style={{ background: C.tooltipBg, border: `1px solid ${C.tooltipBorder}`, color: C.tooltipText }}
      >
        <p className="font-semibold mb-1">{label ? fmtDate(label as string) : ""}</p>
        {payload.map((p) => (
          <p key={p.name} style={{ color: p.color }}>
            {CATEGORY_LABELS[p.name] ?? p.name.replace(/_/g, " ")}: <span className="font-mono">{p.value}</span>
          </p>
        ))}
      </div>
    );
  };

  return (
    <div>
      {/* Custom legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1.5 mb-4">
        {ALL_CATEGORIES.map((cat) => (
          <span key={cat} className="flex items-center gap-1.5 text-[11px]" style={{ color: C.tick }}>
            <span
              className="inline-block h-2 w-2 rounded-full shrink-0"
              style={{ background: CATEGORY_COLORS[cat] }}
            />
            {CATEGORY_LABELS[cat] ?? cat.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
        <XAxis
          dataKey="date"
          tickFormatter={fmtDate}
          tick={{ fontSize: 10, fill: C.tick }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: C.tick }}
          axisLine={false}
          tickLine={false}
          width={28}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} />
        {ALL_CATEGORIES.map((cat) => (
          <Area
            key={cat}
            type="monotone"
            dataKey={cat}
            stackId="a"
            stroke={CATEGORY_COLORS[cat]}
            fill={CATEGORY_COLORS[cat]}
            fillOpacity={0.7}
            strokeWidth={1.5}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
    </div>
  );
}
