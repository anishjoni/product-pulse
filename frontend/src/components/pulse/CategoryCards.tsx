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
    <div className="grid grid-cols-2 gap-px sm:grid-cols-3 lg:grid-cols-5 bg-border rounded-sm overflow-hidden">
      {ALL_CATEGORIES.map((cat) => {
        const count = counts[cat] ?? 0;
        const pct = total > 0 ? ((count / total) * 100).toFixed(0) : "0";
        const isSelected = selectedCategory === cat;
        const color = CATEGORY_COLORS[cat];

        return (
          <div
            key={cat}
            role="button"
            tabIndex={0}
            aria-pressed={isSelected}
            aria-label={`${CATEGORY_LABELS[cat]}: ${count} items`}
            className={`
              relative flex flex-col justify-between p-4 cursor-pointer transition-colors
              focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-inset
              ${isSelected ? "bg-card" : "bg-background hover:bg-card"}
            `}
            onClick={() => onSelect(isSelected ? null : cat)}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(isSelected ? null : cat)}
          >
            {/* Left accent bar */}
            <div
              className="absolute left-0 top-0 bottom-0 w-[3px] transition-opacity"
              style={{ backgroundColor: color, opacity: isSelected ? 1 : 0.3 }}
            />

            <div className="pl-1">
              <p className="font-display text-[10px] font-semibold tracking-[0.18em] uppercase text-muted-foreground mb-3">
                {CATEGORY_LABELS[cat]}
              </p>
              <p
                className="font-mono text-3xl font-medium leading-none tabular-nums"
                style={{ color: isSelected ? color : "hsl(var(--foreground))" }}
              >
                {count}
              </p>
              <p className="font-mono text-[11px] text-muted-foreground mt-2 tabular-nums">
                {pct}%
              </p>
            </div>

            {isSelected && (
              <div
                className="absolute bottom-0 left-0 right-0 h-[2px]"
                style={{ backgroundColor: color }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
