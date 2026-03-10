"use client";

import { useState, useEffect } from "react";
import type { FeedbackItem } from "@/lib/api";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatRelativeTime } from "@/lib/utils";

interface TopPostsPanelProps {
  items: FeedbackItem[];
  selectedCategory: string | null;
  slug: string;
  topK?: number;
}

export function TopPostsPanel({ items, selectedCategory, slug, topK = 5 }: TopPostsPanelProps) {
  const [open, setOpen] = useState(false);

  // Auto-expand when a category is selected
  useEffect(() => {
    if (selectedCategory) setOpen(true);
  }, [selectedCategory]);

  const filtered = selectedCategory
    ? items.filter((i) => i.category === selectedCategory)
    : items;

  const top = filtered.slice(0, topK);

  const feedUrl = selectedCategory
    ? `/products/${slug}/feed?category=${selectedCategory}`
    : `/products/${slug}/feed`;

  const categoryColor = selectedCategory ? CATEGORY_COLORS[selectedCategory] : null;

  return (
    <div className="rounded border border-border bg-card overflow-hidden">
      {/* Header — clickable to collapse */}
      <button
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-muted/40 transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Top posts</span>
          {selectedCategory && categoryColor && (
            <span
              className="text-[10px] px-1.5 py-0.5 rounded font-medium"
              style={{
                background: `${categoryColor}22`,
                color: categoryColor,
              }}
            >
              {CATEGORY_LABELS[selectedCategory] ?? selectedCategory}
            </span>
          )}
          <span className="text-[10px] text-muted-foreground tabular-nums">
            {filtered.length} total
          </span>
        </div>
        {/* Chevron */}
        <svg
          width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          className={`text-muted-foreground transition-transform duration-150 ${open ? "" : "-rotate-90"}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Body */}
      {open && (
        <>
          {top.length === 0 ? (
            <p className="px-4 py-6 text-sm text-center text-muted-foreground">No posts yet.</p>
          ) : (
            <div className="divide-y divide-border">
              {top.map((item) => {
                const color = CATEGORY_COLORS[item.category] ?? "#6B7280";
                const sentColor =
                  item.sentiment > 0.05
                    ? "var(--color-positive)"
                    : item.sentiment < -0.05
                    ? "var(--color-negative)"
                    : "var(--color-ink-dim)";

                return (
                  <div key={item.id} className="flex items-stretch">
                    <div className="w-[3px] shrink-0" style={{ background: color }} />
                    <div className="px-4 py-2.5 min-w-0 flex-1">
                      <p className="text-sm leading-snug line-clamp-2">{item.summary}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span
                          className="text-[10px] uppercase tracking-wide font-medium"
                          style={{ color }}
                        >
                          {CATEGORY_LABELS[item.category] ?? item.category}
                        </span>
                        <span
                          className="text-[10px] tabular-nums"
                          style={{ color: sentColor }}
                        >
                          {item.sentiment > 0 ? "+" : ""}
                          {item.sentiment.toFixed(2)}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {formatRelativeTime(item.fetched_at)}
                        </span>
                        {item.url && (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] ml-auto hover:opacity-80 transition-opacity"
                            style={{ color: "var(--color-signal)" }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            ↗
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Footer */}
          <div
            className="px-4 py-2 border-t border-border flex justify-end"
            style={{ background: "var(--color-surface-base)" }}
          >
            <a
              href={feedUrl}
              className="text-[10px] transition-colors hover:text-foreground"
              style={{ color: "var(--color-ink-dim)" }}
            >
              View all in feed →
            </a>
          </div>
        </>
      )}
    </div>
  );
}
