"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatRelativeTime } from "@/lib/utils";
import type { FeedbackItem } from "@/lib/api";
import { getFeedbackItem } from "@/lib/api";

interface FeedCardProps {
  item: FeedbackItem;
}

function sentimentColor(s: number): string {
  if (s > 0.3) return "#22C55E";
  if (s < -0.3) return "#EF4444";
  return "#6B7280";
}

function sentimentLabel(s: number): string {
  if (s > 0.3) return "Positive";
  if (s < -0.3) return "Negative";
  return "Neutral";
}

export function FeedCard({ item }: FeedCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [rawContent, setRawContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleExpand() {
    if (!expanded && rawContent === null) {
      setLoading(true);
      try {
        const detail = await getFeedbackItem(item.id);
        setRawContent(detail.content);
      } catch {
        setRawContent("Failed to load content.");
      } finally {
        setLoading(false);
      }
    }
    setExpanded((v) => !v);
  }

  const catColor = CATEGORY_COLORS[item.category] ?? "#6B7280";
  const catLabel = CATEGORY_LABELS[item.category] ?? item.category;

  return (
    <Card className="transition-shadow hover:shadow-sm">
      <CardContent className="p-4 space-y-2">
        {/* Top row: badges + date */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge style={{ backgroundColor: catColor, color: "#fff", border: "none" }}>
            {catLabel}
          </Badge>
          <Badge variant="outline" className="capitalize">
            {item.source_ref}
          </Badge>
          {item.confidence < 0.7 && (
            <Badge variant="outline" className="text-yellow-600 border-yellow-400">
              Low confidence
            </Badge>
          )}
          <span className="ml-auto text-xs text-muted-foreground">
            {formatRelativeTime(item.fetched_at)}
          </span>
        </div>

        {/* LLM summary */}
        <p className="text-sm font-medium leading-snug">{item.summary || "No summary."}</p>

        {/* Sentiment + score */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: sentimentColor(item.sentiment) }}
            />
            {sentimentLabel(item.sentiment)} ({item.sentiment.toFixed(2)})
          </span>
          {item.score != null && <span>Score: {item.score}</span>}
          {item.author && <span>by {item.author}</span>}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-500 hover:underline"
            >
              View original ↗
            </a>
          )}
          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={handleExpand}>
            {loading ? "Loading…" : expanded ? "Collapse" : "Show raw"}
          </Button>
        </div>

        {/* Expandable raw content */}
        {expanded && rawContent !== null && (
          <pre className="mt-2 max-h-48 overflow-y-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap">
            {rawContent}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}
