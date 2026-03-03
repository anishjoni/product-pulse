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
    if (dayMap[day]) {
      dayMap[day].push(item.sentiment);
    }
  }

  return Object.entries(dayMap).map(([date, sentiments]) => ({
    date: date.slice(5), // MM-DD
    avg:
      sentiments.length > 0
        ? parseFloat(
            (sentiments.reduce((s, v) => s + v, 0) / sentiments.length).toFixed(3)
          )
        : null,
  }));
}

export function SentimentTimeline({ feedbackItems }: SentimentTimelineProps) {
  const data = buildDailyData(feedbackItems);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ left: 0, right: 16, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} tickCount={5} />
        <Tooltip
          formatter={(v) => {
            const num = typeof v === "number" ? v : null;
            return num !== null ? [num.toFixed(3), "Avg Sentiment"] : ["No data", ""];
          }}
        />
        <ReferenceLine y={0} stroke="#94A3B8" strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="avg"
          dot={false}
          connectNulls
          stroke="#3B82F6"
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
