"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ALL_CATEGORIES, CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/utils";
import type { CategoryCounts } from "@/lib/api";

interface PulseScoreBarProps {
  counts: CategoryCounts;
  selectedCategory: string | null;
  onCategoryClick?: (category: string | null) => void;
  connected?: boolean;
}

export function PulseScoreBar({ counts, selectedCategory, onCategoryClick, connected }: PulseScoreBarProps) {
  const total = ALL_CATEGORIES.reduce((sum, c) => sum + (counts[c] ?? 0), 0);
  if (total === 0) return null;

  return (
    <TooltipProvider>
      <div
        className={`flex w-full overflow-hidden ${connected ? "rounded-t-md" : "rounded-md"}`}
        style={{ height: 60 }}
      >
        {ALL_CATEGORIES.map((cat) => {
          const count = counts[cat] ?? 0;
          if (count === 0) return null;
          const pct = (count / total) * 100;
          const isSelected = selectedCategory === cat;
          const dimmed = selectedCategory !== null && !isSelected;

          return (
            <Tooltip key={cat}>
              <TooltipTrigger asChild>
                <button
                  className="relative flex flex-col justify-center px-3 transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: CATEGORY_COLORS[cat],
                    opacity: dimmed ? 0.4 : 1,
                  }}
                  onClick={() => onCategoryClick?.(isSelected ? null : cat)}
                  aria-pressed={isSelected}
                  aria-label={`${CATEGORY_LABELS[cat]}: ${count} items`}
                >
                  {pct >= 12 && (
                    <>
                      <span
                        className="text-[10px] font-medium leading-none truncate"
                        style={{ color: cat === "general_discussion" ? "#33291A" : "rgba(255,255,255,0.85)" }}
                      >
                        {CATEGORY_LABELS[cat]}
                      </span>
                      <span
                        className="font-bold leading-tight tabular-nums"
                        style={{ fontFamily: "var(--font-geist-mono)", fontSize: 20, color: cat === "general_discussion" ? "#1A160D" : "#ffffff" }}
                      >
                        {count}
                      </span>
                    </>
                  )}
                  {isSelected && (
                    <span
                      className="absolute bottom-0 left-0 right-0 h-[3px]"
                      style={{ background: cat === "general_discussion" ? "rgba(0,0,0,0.3)" : "rgba(255,255,255,0.5)" }}
                    />
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="font-semibold text-xs">{CATEGORY_LABELS[cat]}</p>
                <p className="text-muted-foreground text-xs">
                  {count} items · {pct.toFixed(1)}%
                </p>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
