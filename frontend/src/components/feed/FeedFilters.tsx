"use client";

import { useEffect, useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
    <div className="sticky top-0 z-10 border-b border-border py-3 px-4 space-y-2.5"
      style={{ background: "var(--color-surface-card)" }}
    >
      {/* Category pills */}
      <div className="flex flex-wrap gap-1.5">
        {ALL_CATEGORIES.map((cat) => {
          const active = params.category === cat;
          const color = CATEGORY_COLORS[cat];
          return (
            <button
              key={cat}
              onClick={() => toggleCategory(cat)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors border"
              style={
                active
                  ? {
                      borderColor: color,
                      color: color,
                      background: `${color}18`,
                    }
                  : {
                      borderColor: "var(--color-wire)",
                      color: "var(--color-ink-dim)",
                    }
              }
            >
              <span
                className="h-1.5 w-1.5 rounded-full shrink-0"
                style={{ backgroundColor: color }}
              />
              {CATEGORY_LABELS[cat]}
            </button>
          );
        })}
        {params.category && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs text-muted-foreground"
            onClick={() => onChange({ ...params, category: undefined, page: 1 })}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Controls row */}
      <div className="flex flex-wrap gap-2 items-center">
        <Select
          value={params.source ?? "all"}
          onValueChange={(v) =>
            onChange({ ...params, source: v === "all" ? undefined : v, page: 1 })
          }
        >
          <SelectTrigger className="w-32 h-8 text-xs">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sources</SelectItem>
            <SelectItem value="reddit">Reddit</SelectItem>
            <SelectItem value="youtube">YouTube</SelectItem>
            <SelectItem value="google_play">Google Play</SelectItem>
            <SelectItem value="apple_app_store">App Store</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={params.sentiment ?? "all"}
          onValueChange={(v) =>
            onChange({ ...params, sentiment: v === "all" ? undefined : v, page: 1 })
          }
        >
          <SelectTrigger className="w-36 h-8 text-xs">
            <SelectValue placeholder="Sentiment" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sentiment</SelectItem>
            <SelectItem value="positive">Positive</SelectItem>
            <SelectItem value="neutral">Neutral</SelectItem>
            <SelectItem value="negative">Negative</SelectItem>
          </SelectContent>
        </Select>

        <Input
          placeholder="Search…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-48 h-8 text-xs"
        />

        <Input
          type="date"
          value={params.date_from ?? ""}
          onChange={(e) =>
            onChange({ ...params, date_from: e.target.value || undefined, page: 1 })
          }
          className="w-36 h-8 text-xs"
          aria-label="From date"
        />
        <Input
          type="date"
          value={params.date_to ?? ""}
          onChange={(e) =>
            onChange({ ...params, date_to: e.target.value || undefined, page: 1 })
          }
          className="w-36 h-8 text-xs"
          aria-label="To date"
        />
      </div>
    </div>
  );
}
