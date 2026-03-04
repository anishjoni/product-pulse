"use client";

import { useState } from "react";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatRelativeTime } from "@/lib/utils";
import type { FeedbackItem } from "@/lib/api";
import { getFeedbackItem } from "@/lib/api";

interface FeedCardProps {
  item: FeedbackItem;
}

function sentimentStyle(s: number): { label: string; color: string } {
  if (s > 0.3) return { label: "Positive", color: "var(--color-positive)" };
  if (s < -0.3) return { label: "Negative", color: "var(--color-negative)" };
  return { label: "Neutral", color: "var(--color-ink-dim)" };
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

  const catColor = CATEGORY_COLORS[item.category] ?? "var(--color-ink-faint)";
  const catLabel = CATEGORY_LABELS[item.category] ?? item.category;
  const sent = sentimentStyle(item.sentiment);

  return (
    <div
      className="rounded bg-card border border-border overflow-hidden transition-colors hover:border-muted-foreground/30"
    >
      <div className="flex">
        {/* Category color stripe */}
        <div className="w-[3px] shrink-0" style={{ backgroundColor: catColor }} />

        <div className="px-4 py-3 flex-1 min-w-0 space-y-2">
          {/* Top meta row */}
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-[10px] font-medium uppercase tracking-wide"
              style={{ color: catColor }}
            >
              {catLabel}
            </span>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
              {item.source_ref}
            </span>
            {item.confidence < 0.7 && (
              <span className="text-[10px] text-yellow-500/80">low confidence</span>
            )}
            <span className="ml-auto text-[10px] text-muted-foreground tabular-nums">
              {formatRelativeTime(item.fetched_at)}
            </span>
          </div>

          {/* Summary — dominant element */}
          <p className="text-sm leading-snug">{item.summary || "No summary."}</p>

          {/* Metadata row */}
          <div className="flex items-center gap-3 text-[11px]" style={{ color: "var(--color-ink-faint)" }}>
            <span className="flex items-center gap-1">
              <span
                className="inline-block h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: sent.color }}
              />
              <span style={{ color: sent.color }}>{sent.label}</span>
            </span>
            {item.score != null && (
              <span className="tabular-nums">{item.score} pts</span>
            )}
            {item.author && <span>by {item.author}</span>}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] transition-colors"
                style={{ color: "var(--color-signal)" }}
              >
                View original ↗
              </a>
            )}
            <button
              className="text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              onClick={handleExpand}
            >
              {loading ? "Loading…" : expanded ? "Collapse" : "Show raw"}
            </button>
          </div>

          {/* Expandable raw */}
          {expanded && rawContent !== null && (
            <pre
              className="max-h-48 overflow-y-auto rounded p-3 text-[11px] whitespace-pre-wrap border border-border"
              style={{ background: "var(--color-surface-base)" }}
            >
              {rawContent}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
