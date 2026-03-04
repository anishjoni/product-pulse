"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FeedCard } from "@/components/feed/FeedCard";
import { FeedFilters } from "@/components/feed/FeedFilters";
import { Button } from "@/components/ui/button";
import {
  getProducts,
  getProductFeedback,
  type FeedbackItem,
  type FeedbackQueryParams,
} from "@/lib/api";

export default function FeedPage({ params }: { params: { slug: string } }) {
  const searchParams = useSearchParams();
  const [productId, setProductId] = useState<number | null>(null);
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<FeedbackQueryParams>({
    page: 1,
    page_size: 20,
    category: searchParams.get("category") ?? undefined,
  });

  useEffect(() => {
    getProducts().then((ps) => {
      const p = ps.find((x) => x.slug === params.slug);
      if (p) setProductId(p.id);
    });
  }, [params.slug]);

  const loadFeed = useCallback(async () => {
    if (!productId) return;
    setLoading(true);
    try {
      const res = await getProductFeedback(productId, filters);
      setItems(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } finally {
      setLoading(false);
    }
  }, [productId, filters]);

  useEffect(() => { loadFeed(); }, [loadFeed]);

  return (
    <div className="flex flex-col">
      <FeedFilters params={filters} onChange={setFilters} />

      <div className="p-4 max-w-3xl mx-auto w-full space-y-3">
        <p className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground">
          {loading ? "LOADING…" : `${total} ITEMS`}
        </p>

        {items.map((item) => (
          <FeedCard key={item.id} item={item} />
        ))}

        {pages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-6">
            <Button
              variant="ghost"
              size="sm"
              disabled={filters.page === 1}
              className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground hover:text-foreground h-7 px-3"
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
            >
              ← PREV
            </Button>
            <span className="font-mono text-[10px] tracking-widest text-muted-foreground tabular-nums">
              {filters.page} / {pages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              disabled={filters.page === pages}
              className="font-mono text-[10px] tracking-widest uppercase text-muted-foreground hover:text-foreground h-7 px-3"
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
            >
              NEXT →
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
