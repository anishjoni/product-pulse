"use client";

import type { FeedbackItem } from "@/lib/api";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatRelativeTime } from "@/lib/utils";

interface BleedWellProps {
  items: FeedbackItem[];
  category: string;
  slug: string;
  topK?: number;
}

export function BleedWell({ items, category, slug, topK = 5 }: BleedWellProps) {
  const color = CATEGORY_COLORS[category] ?? "#6B7280";
  const top = items.filter((i) => i.category === category).slice(0, topK);
  const total = items.filter((i) => i.category === category).length;

  return (
    <div
      className="rounded-b-md overflow-hidden"
      style={{
        background: `${color}0f`,
        borderLeft: `1px solid ${color}30`,
        borderRight: `1px solid ${color}30`,
        borderBottom: `1px solid ${color}30`,
      }}
    >
      {top.length === 0 ? (
        <p className="px-4 py-5 text-sm text-center text-muted-foreground">No posts in this category yet.</p>
      ) : (
        <div>
          {top.map((item, i) => {
            const sentColor =
              item.sentiment > 0.05
                ? "var(--color-positive)"
                : item.sentiment < -0.05
                ? "var(--color-negative)"
                : "var(--color-ink-dim)";

            return (
              <div
                key={item.id}
                className="flex items-stretch"
                style={{
                  borderBottom: i < top.length - 1 ? `1px solid ${color}18` : undefined,
                }}
              >
                <div className="w-[3px] shrink-0" style={{ background: color }} />
                <div className="px-4 py-2.5 min-w-0 flex-1">
                  <p className="text-sm leading-snug line-clamp-2">{item.summary}</p>
                  <div className="flex items-center gap-3 mt-1">
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
                    {item.url && item.source !== "google_play" && item.source !== "apple_app_store" && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] ml-auto hover:opacity-80 transition-opacity"
                        style={{ color }}
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
      <div className="px-4 py-2 flex items-center justify-between">
        <span className="text-[10px] text-muted-foreground">
          {CATEGORY_LABELS[category]} · {total} total
        </span>
        <a
          href={`/products/${slug}/feed?category=${category}`}
          className="text-[10px] transition-opacity hover:opacity-80"
          style={{ color }}
        >
          View all in feed →
        </a>
      </div>
    </div>
  );
}
