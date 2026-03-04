"use client";

import { useEffect, useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ALL_CATEGORIES, CATEGORY_COLORS, CATEGORY_LABELS } from "@/lib/utils";
import type { FeedbackQueryParams } from "@/lib/api";

interface FeedFiltersProps {
  params: FeedbackQueryParams;
  onChange: (params: FeedbackQueryParams) => void;
}

export function FeedFilters({ params, onChange }: FeedFiltersProps) {
  const [search, setSearch] = useState(params.search ?? "");

  useEffect(() => {
    const t = setTimeout(() => {
      onChange({ ...params, search: search || undefined, page: 1 });
    }, 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const toggleCategory = useCallback(
    (cat: string) => {
      onChange({ ...params, category: params.category === cat ? undefined : cat, page: 1 });
    },
    [params, onChange]
  );

  return (
    <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 border-b border-border">
      {/* Category pills */}
      <div className="flex flex-wrap gap-px px-4 pt-3 pb-0">
        {ALL_CATEGORIES.map((cat) => {
          const active = params.category === cat;
          const color = CATEGORY_COLORS[cat];
          return (
            <button
              key={cat}
              type="button"
              role="button"
              tabIndex={0}
              aria-pressed={active}
              className="font-display text-[10px] font-semibold tracking-[0.16em] uppercase px-3 py-1 rounded-sm transition-all select-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              style={
                active
                  ? { backgroundColor: `${color}22`, color, border: `1px solid ${color}55` }
                  : { backgroundColor: "transparent", color: "#6b6560", border: "1px solid transparent" }
              }
              onClick={() => toggleCategory(cat)}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && toggleCategory(cat)}
            >
              {CATEGORY_LABELS[cat]}
            </button>
          );
        })}
        {params.category && (
          <button
            type="button"
            className="font-mono text-[10px] tracking-widest uppercase px-3 py-1 text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => onChange({ ...params, category: undefined, page: 1 })}
          >
            CLEAR ×
          </button>
        )}
      </div>

      {/* Row 2: selects + search + dates */}
      <div className="flex flex-wrap gap-2 items-center px-4 py-2">
        <Select
          value={params.source ?? "all"}
          onValueChange={(v) =>
            onChange({ ...params, source: v === "all" ? undefined : v, page: 1 })
          }
        >
          <SelectTrigger className="h-7 w-28 font-mono text-[10px] tracking-widest uppercase border-border bg-transparent">
            <SelectValue placeholder="SOURCE" />
          </SelectTrigger>
          <SelectContent className="font-mono text-[10px] tracking-widest uppercase">
            <SelectItem value="all">ALL</SelectItem>
            <SelectItem value="reddit">REDDIT</SelectItem>
            <SelectItem value="youtube">YOUTUBE</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={params.sentiment ?? "all"}
          onValueChange={(v) =>
            onChange({ ...params, sentiment: v === "all" ? undefined : v, page: 1 })
          }
        >
          <SelectTrigger className="h-7 w-32 font-mono text-[10px] tracking-widest uppercase border-border bg-transparent">
            <SelectValue placeholder="SENTIMENT" />
          </SelectTrigger>
          <SelectContent className="font-mono text-[10px] tracking-widest uppercase">
            <SelectItem value="all">ALL</SelectItem>
            <SelectItem value="positive">POS</SelectItem>
            <SelectItem value="neutral">NEU</SelectItem>
            <SelectItem value="negative">NEG</SelectItem>
          </SelectContent>
        </Select>

        <Input
          placeholder="Search…"
          aria-label="Search feedback"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-7 w-44 font-mono text-[11px] border-border bg-transparent placeholder:text-muted-foreground/50"
        />

        <Input
          type="date"
          aria-label="From date"
          value={params.date_from ?? ""}
          onChange={(e) =>
            onChange({ ...params, date_from: e.target.value || undefined, page: 1 })
          }
          className="h-7 w-32 font-mono text-[10px] border-border bg-transparent"
          title="From date"
        />
        <Input
          type="date"
          aria-label="To date"
          value={params.date_to ?? ""}
          onChange={(e) =>
            onChange({ ...params, date_to: e.target.value || undefined, page: 1 })
          }
          className="h-7 w-32 font-mono text-[10px] border-border bg-transparent"
          title="To date"
        />
      </div>
    </div>
  );
}
