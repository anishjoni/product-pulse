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

const GRID     = "#262420";
const ZERO     = "#3d3a36";
const LINE     = "#f59e0b";
const TICK     = "#6b6560";
const BG_TIP   = "#141210";
const BDR_TIP  = "#2a2620";

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
    avg: sentiments.length > 0
      ? parseFloat((sentiments.reduce((s, v) => s + v, 0) / sentiments.length).toFixed(3))
      : null,
  }));
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  const v = payload[0]?.value;
  const color = v > 0.1 ? "#3fb950" : v < -0.1 ? "#f85149" : TICK;
  return (
    <div style={{ background: BG_TIP, border: `1px solid ${BDR_TIP}`, padding: "8px 12px", borderRadius: 2 }}>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: TICK, letterSpacing: "0.1em", marginBottom: 4 }}>{label}</p>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 13, color, fontWeight: 500 }}>
        {v != null ? (v >= 0 ? "+" : "") + v.toFixed(3) : "—"}
      </p>
    </div>
  );
};

export function SentimentTimeline({ feedbackItems }: SentimentTimelineProps) {
  const data = buildDailyData(feedbackItems);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ left: 0, right: 16, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="2 4" stroke={GRID} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: TICK, fontFamily: "var(--font-mono)" }}
          axisLine={{ stroke: GRID }}
          tickLine={false}
        />
        <YAxis
          domain={[-1, 1]}
          tick={{ fontSize: 10, fill: TICK, fontFamily: "var(--font-mono)" }}
          tickCount={5}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={0} stroke={ZERO} strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="avg"
          dot={false}
          connectNulls
          stroke={LINE}
          strokeWidth={1.5}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
