"use client";

import { Card, CardContent } from "@/components/ui/card";
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
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {ALL_CATEGORIES.map((cat) => {
        const count = counts[cat] ?? 0;
        const pct = total > 0 ? ((count / total) * 100).toFixed(0) : "0";
        const isSelected = selectedCategory === cat;

        return (
          <Card
            key={cat}
            role="button"
            tabIndex={0}
            aria-pressed={isSelected}
            aria-label={`${CATEGORY_LABELS[cat]}: ${count} items`}
            className={`cursor-pointer transition-all hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 ${
              isSelected ? "ring-2 ring-offset-1" : ""
            }`}
            style={isSelected ? { outline: `2px solid ${CATEGORY_COLORS[cat]}` } : {}}
            onClick={() => onSelect(isSelected ? null : cat)}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(isSelected ? null : cat)}
          >
            <CardContent className="p-4">
              <div
                className="mb-1 h-1 w-8 rounded-full"
                style={{ backgroundColor: CATEGORY_COLORS[cat] }}
              />
              <p className="text-xs text-muted-foreground">{CATEGORY_LABELS[cat]}</p>
              <p className="text-2xl font-bold">{count}</p>
              <p className="text-xs text-muted-foreground">{pct}% of total</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
