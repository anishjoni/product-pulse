"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ALL_CATEGORIES, CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/utils";
import type { CategoryCounts } from "@/lib/api";

interface PulseScoreBarProps {
  counts: CategoryCounts;
  onCategoryClick?: (category: string) => void;
}

export function PulseScoreBar({ counts, onCategoryClick }: PulseScoreBarProps) {
  const total = ALL_CATEGORIES.reduce((sum, c) => sum + (counts[c] ?? 0), 0);
  if (total === 0) return null;

  return (
    <TooltipProvider>
      <div className="flex h-8 w-full overflow-hidden rounded-lg">
        {ALL_CATEGORIES.map((cat) => {
          const count = counts[cat] ?? 0;
          if (count === 0) return null;
          const pct = ((count / total) * 100).toFixed(1);
          return (
            <Tooltip key={cat}>
              <TooltipTrigger asChild>
                <div
                  className="cursor-pointer transition-opacity hover:opacity-80"
                  style={{
                    width: `${(count / total) * 100}%`,
                    backgroundColor: CATEGORY_COLORS[cat],
                  }}
                  onClick={() => onCategoryClick?.(cat)}
                />
              </TooltipTrigger>
              <TooltipContent>
                <p className="font-semibold">{CATEGORY_LABELS[cat]}</p>
                <p>
                  {count} items &middot; {pct}%
                </p>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
