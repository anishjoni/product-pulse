"use client";

import { ALL_CATEGORIES, CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/utils";
import type { CategoryCounts } from "@/lib/api";

interface CategoryCardsProps {
  counts: CategoryCounts;
  selectedCategory: string | null;
  onSelect: (category: string | null) => void;
}

export function CategoryCards({ counts, selectedCategory, onSelect }: CategoryCardsProps) {
  const total = ALL_CATEGORIES.reduce((sum, c) => sum + (counts[c] ?? 0), 0);

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
      {ALL_CATEGORIES.map((cat) => {
        const count = counts[cat] ?? 0;
        const pct = total > 0 ? ((count / total) * 100).toFixed(0) : "0";
        const isSelected = selectedCategory === cat;
        const color = CATEGORY_COLORS[cat];

        return (
          <button
            key={cat}
            className="text-left rounded bg-card border border-border transition-colors hover:border-border focus:outline-none focus-visible:ring-1 focus-visible:ring-ring overflow-hidden"
            style={
              isSelected
                ? { borderColor: color, boxShadow: `0 0 0 1px ${color}` }
                : undefined
            }
            onClick={() => onSelect(isSelected ? null : cat)}
            aria-pressed={isSelected}
          >
            <div className="flex h-full">
              {/* Left color stripe */}
              <div
                className="w-[3px] shrink-0 self-stretch"
                style={{ backgroundColor: color }}
              />
              <div className="px-3 py-3 min-w-0">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wide truncate mb-0.5">
                  {CATEGORY_LABELS[cat]}
                </p>
                <p
                  className="font-bold tabular-nums leading-none"
                  style={{ fontFamily: "var(--font-geist-mono)", fontSize: 22 }}
                >
                  {count}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">{pct}% of total</p>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
