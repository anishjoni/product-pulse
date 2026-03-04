"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { FeedbackItem } from "@/lib/api";
import { useTheme } from "@/contexts/theme";

interface SentimentTimelineProps {
  feedbackItems: FeedbackItem[];
}

function buildDailyData(items: FeedbackItem[]) {
  const dayMap: Record<string, number[]> = {};
  const now = new Date();

  for (let i = 13; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    dayMap[key] = [];
  }

  for (const item of items) {
    const day = item.fetched_at.slice(0, 10);
    if (dayMap[day]) dayMap[day].push(item.sentiment);
  }

  return Object.entries(dayMap).map(([date, sentiments]) => ({
    date: date.slice(5),
    avg:
      sentiments.length > 0
        ? parseFloat(
            (sentiments.reduce((s, v) => s + v, 0) / sentiments.length).toFixed(3)
          )
        : null,
  }));
}

export function SentimentTimeline({ feedbackItems }: SentimentTimelineProps) {
  const { isDark } = useTheme();
  const data = buildDailyData(feedbackItems);

  const C = isDark
    ? { grid: "#21262D", tick: "#484F58", zero: "#30363D", signal: "#6366F1", tooltipBg: "#1C2333", tooltipBorder: "#30363D", tooltipText: "#E6EDF3" }
    : { grid: "#E5E7EB", tick: "#9CA3AF", zero: "#D1D5DB", signal: "#6366F1", tooltipBg: "#FFFFFF",  tooltipBorder: "#E5E7EB",  tooltipText: "#111827" };

  const CustomTooltip = ({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: { value: number | null }[];
    label?: string;
  }) => {
    if (!active || !payload?.length) return null;
    const val = payload[0].value;
    return (
      <div
        className="rounded px-3 py-2 text-xs"
        style={{ background: C.tooltipBg, border: `1px solid ${C.tooltipBorder}`, color: C.tooltipText }}
      >
        <p className="font-medium mb-0.5">{label}</p>
        <p style={{ color: C.tick }}>{val !== null ? val.toFixed(3) : "No data"}</p>
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: C.tick }} axisLine={false} tickLine={false} />
        <YAxis domain={[-1, 1]} tick={{ fontSize: 10, fill: C.tick }} tickCount={5} axisLine={false} tickLine={false} width={28} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={0} stroke={C.zero} strokeWidth={1.5} />
        <Line type="monotone" dataKey="avg" dot={false} connectNulls stroke={C.signal} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
