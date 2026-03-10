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
  const [keywords, setKeywords] = useState<string[]>([]);
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
      if (p) { setProductId(p.id); setKeywords(p.keywords ?? []); }
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

  function handleFiltersChange(next: FeedbackQueryParams) {
    setFilters(next);
  }

  return (
    <div className="flex flex-col">
      <FeedFilters params={filters} onChange={handleFiltersChange} />

      <div className="p-4 max-w-3xl mx-auto w-full space-y-3">
        <p className="text-sm text-muted-foreground">
          {loading ? "Loading…" : `${total} items`}
        </p>

        {items.map((item) => (
          <FeedCard key={item.id} item={item} keywords={keywords} />
        ))}

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-4">
            <Button
              variant="outline"
              size="sm"
              disabled={filters.page === 1}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
            >
              Previous
            </Button>
            <span className="text-sm">
              Page {filters.page} of {pages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={filters.page === pages}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
