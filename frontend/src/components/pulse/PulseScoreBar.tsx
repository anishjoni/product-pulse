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
      <div className="flex h-10 w-full overflow-hidden rounded-sm gap-px bg-border">
        {ALL_CATEGORIES.map((cat) => {
          const count = counts[cat] ?? 0;
          if (count === 0) return null;
          const pct = ((count / total) * 100).toFixed(1);
          return (
            <Tooltip key={cat}>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  aria-label={`${CATEGORY_LABELS[cat]}: ${count} items, ${pct}%`}
                  className="relative group cursor-pointer transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-inset overflow-hidden"
                  style={{
                    width: `${(count / total) * 100}%`,
                    backgroundColor: CATEGORY_COLORS[cat],
                    border: "none",
                    padding: 0,
                    height: "100%",
                  }}
                  onClick={() => onCategoryClick?.(cat)}
                >
                  {/* Percentage label — shown only if wide enough */}
                  {(count / total) * 100 > 10 && (
                    <span className="absolute inset-0 flex items-center justify-center font-mono text-[10px] font-medium text-white/80 tabular-nums">
                      {pct}%
                    </span>
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent className="font-sans">
                <p className="font-display font-semibold text-xs tracking-wide">{CATEGORY_LABELS[cat]}</p>
                <p className="font-mono text-xs text-muted-foreground mt-0.5">
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
