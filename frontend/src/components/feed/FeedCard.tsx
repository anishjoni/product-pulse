"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatRelativeTime } from "@/lib/utils";
import type { FeedbackItem } from "@/lib/api";
import { getFeedbackItem } from "@/lib/api";

interface FeedCardProps {
  item: FeedbackItem;
}

function sentimentColor(s: number): string {
  if (s > 0.3)  return "#3fb950";
  if (s < -0.3) return "#f85149";
  return "#6b6560";
}

function sentimentLabel(s: number): string {
  if (s > 0.3)  return "POS";
  if (s < -0.3) return "NEG";
  return "NEU";
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

  const catColor = CATEGORY_COLORS[item.category] ?? "#6b6560";
  const catLabel = CATEGORY_LABELS[item.category] ?? item.category;

  return (
    <div className="border border-border bg-card hover:bg-[hsl(30,8%,9%)] transition-colors rounded-sm overflow-hidden">
      {/* Category color bar */}
      <div className="h-[2px] w-full" style={{ backgroundColor: catColor }} />

      <div className="p-4 space-y-3">
        {/* Top row */}
        <div className="flex items-center gap-3 flex-wrap">
          <span
            className="font-display text-[10px] font-semibold tracking-[0.18em] uppercase px-2 py-0.5 rounded-sm"
            style={{ backgroundColor: `${catColor}22`, color: catColor }}
          >
            {catLabel}
          </span>
          <span className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground border border-border px-2 py-0.5 rounded-sm">
            {item.source_ref}
          </span>
          {item.confidence < 0.7 && (
            <span className="font-mono text-[10px] tracking-widest uppercase text-yellow-600 border border-yellow-900/40 px-2 py-0.5 rounded-sm">
              LOW CONF
            </span>
          )}
          <span className="ml-auto font-mono text-[10px] text-muted-foreground tabular-nums">
            {formatRelativeTime(item.fetched_at)}
          </span>
        </div>

        {/* Summary */}
        <p className="text-sm leading-relaxed text-foreground/90">
          {item.summary || "No summary."}
        </p>

        {/* Meta row */}
        <div className="flex items-center gap-4 pt-1">
          <span className="flex items-center gap-1.5">
            <span
              className="h-1.5 w-1.5 rounded-full shrink-0"
              style={{ backgroundColor: sentimentColor(item.sentiment) }}
            />
            <span
              className="font-mono text-[10px] tracking-widest uppercase tabular-nums"
              style={{ color: sentimentColor(item.sentiment) }}
            >
              {sentimentLabel(item.sentiment)}
            </span>
            <span className="font-mono text-[10px] text-muted-foreground tabular-nums">
              {item.sentiment >= 0 ? "+" : ""}{item.sentiment.toFixed(2)}
            </span>
          </span>
          {item.score != null && (
            <span className="font-mono text-[10px] text-muted-foreground">
              ↑{item.score}
            </span>
          )}
          {item.author && (
            <span className="font-mono text-[10px] text-muted-foreground truncate">
              {item.author}
            </span>
          )}

          <div className="ml-auto flex items-center gap-2">
            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono text-[10px] tracking-widest uppercase text-primary hover:text-primary/80 transition-colors"
              >
                SRC ↗
              </a>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="h-5 px-2 font-mono text-[10px] tracking-widest uppercase text-muted-foreground hover:text-foreground"
              onClick={handleExpand}
            >
              {loading ? "…" : expanded ? "HIDE" : "RAW"}
            </Button>
          </div>
        </div>

        {/* Raw content */}
        {expanded && rawContent !== null && (
          <pre className="mt-2 max-h-48 overflow-y-auto bg-background border border-border rounded-sm p-3 font-mono text-[11px] text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {rawContent}
          </pre>
        )}
      </div>
    </div>
  );
}
