"use client";

import { useEffect, useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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

  // Debounce search 300ms
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
    <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b py-3 px-4 space-y-3">
      {/* Category pills */}
      <div className="flex flex-wrap gap-2">
        {ALL_CATEGORIES.map((cat) => {
          const active = params.category === cat;
          return (
            <Badge
              key={cat}
              variant={active ? "default" : "outline"}
              className="cursor-pointer select-none"
              style={active ? { backgroundColor: CATEGORY_COLORS[cat], border: "none" } : {}}
              onClick={() => toggleCategory(cat)}
            >
              {CATEGORY_LABELS[cat]}
            </Badge>
          );
        })}
        {params.category && (
          <Button variant="ghost" size="sm" onClick={() => onChange({ ...params, category: undefined, page: 1 })}>
            Clear
          </Button>
        )}
      </div>

      {/* Row 2: source, sentiment, search */}
      <div className="flex flex-wrap gap-2 items-center">
        <Select
          value={params.source ?? "all"}
          onValueChange={(v) =>
            onChange({ ...params, source: v === "all" ? undefined : v, page: 1 })
          }
        >
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sources</SelectItem>
            <SelectItem value="reddit">Reddit</SelectItem>
            <SelectItem value="youtube">YouTube</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={params.sentiment ?? "all"}
          onValueChange={(v) =>
            onChange({ ...params, sentiment: v === "all" ? undefined : v, page: 1 })
          }
        >
          <SelectTrigger className="w-36">
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
          className="w-48"
        />

        <Input
          type="date"
          value={params.date_from ?? ""}
          onChange={(e) =>
            onChange({ ...params, date_from: e.target.value || undefined, page: 1 })
          }
          className="w-36"
          title="From date"
        />
        <Input
          type="date"
          value={params.date_to ?? ""}
          onChange={(e) =>
            onChange({ ...params, date_to: e.target.value || undefined, page: 1 })
          }
          className="w-36"
          title="To date"
        />
      </div>
    </div>
  );
}
