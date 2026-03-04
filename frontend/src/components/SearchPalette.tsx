"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getProducts, getProductFeedback, type FeedbackItem } from "@/lib/api";
import { CATEGORY_COLORS, CATEGORY_LABELS, formatRelativeTime } from "@/lib/utils";

export function SearchPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [productId, setProductId] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string | undefined;

  // Resolve product ID once
  useEffect(() => {
    if (!slug) return;
    getProducts().then((products) => {
      const p = products.find((x) => x.slug === slug);
      if (p) setProductId(p.id);
    });
  }, [slug]);

  // Ctrl/Cmd+K to open, Escape to close
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Focus + reset when opened
  useEffect(() => {
    if (open) {
      setQuery("");
      setResults([]);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (!query.trim() || !productId) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await getProductFeedback(productId, { search: query.trim(), page_size: 8 });
        setResults(res.items);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query, productId]);

  function goToFeed() {
    if (!slug || !query.trim()) return;
    router.push(`/products/${slug}/feed?search=${encodeURIComponent(query.trim())}`);
    setOpen(false);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[14vh] px-4"
      style={{ background: "rgba(0,0,0,0.55)" }}
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-xl rounded-lg border border-border overflow-hidden shadow-2xl"
        style={{ background: "var(--color-surface-card)" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Input row */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <svg
            width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ color: "var(--color-ink-dim)", flexShrink: 0 }}
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && goToFeed()}
            placeholder="Search posts…"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          {loading && (
            <svg
              className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" style={{ color: "var(--color-ink-faint)" }}
            >
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          )}
          <kbd
            className="text-[10px] border border-border rounded px-1.5 py-0.5 shrink-0"
            style={{ color: "var(--color-ink-faint)" }}
          >
            esc
          </kbd>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="max-h-72 overflow-y-auto">
            {results.map((item) => {
              const color = CATEGORY_COLORS[item.category] ?? "#6B7280";
              return (
                <button
                  key={item.id}
                  className="w-full flex items-stretch text-left transition-colors hover:bg-muted/50 border-b border-border last:border-0"
                  onClick={goToFeed}
                >
                  <div className="w-[3px] shrink-0" style={{ background: color }} />
                  <div className="px-4 py-2.5 min-w-0">
                    <p className="text-sm leading-snug line-clamp-1">{item.summary}</p>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span
                        className="text-[10px] uppercase tracking-wide"
                        style={{ color }}
                      >
                        {CATEGORY_LABELS[item.category] ?? item.category}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {formatRelativeTime(item.fetched_at)}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Footer */}
        <div
          className="px-4 py-2 flex items-center justify-between border-t border-border"
          style={{ background: "var(--color-surface-base)" }}
        >
          <span className="text-[10px]" style={{ color: "var(--color-ink-faint)" }}>
            {!query.trim()
              ? "Type to search posts"
              : loading
              ? "Searching…"
              : results.length > 0
              ? `${results.length} results`
              : "No results"}
          </span>
          {query.trim() && (
            <span className="text-[10px]" style={{ color: "var(--color-ink-faint)" }}>
              ↵ see all in feed
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
