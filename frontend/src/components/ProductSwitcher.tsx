"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { Product } from "@/lib/api";

interface ProductSwitcherProps {
  products: Product[];
  currentSlug: string;
}

export function ProductSwitcher({ products, currentSlug }: ProductSwitcherProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const router = useRouter();

  const current = products.find((p) => p.slug === currentSlug);

  // Preserve the current tab when switching products
  const segments = pathname.split("/"); // ['', 'products', 'slug', 'tab']
  const currentTab = segments[4] ?? "dashboard";

  // Close on outside click
  useEffect(() => {
    function onPointerDown(e: PointerEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  function switchTo(slug: string) {
    setOpen(false);
    router.push(`/products/${slug}/${currentTab}`);
  }

  if (!current) return null;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors max-w-[160px] min-w-0"
      >
        <span className="truncate">{current.name}</span>
        <svg
          width="11" height="11" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          className={`shrink-0 transition-transform duration-150 ${open ? "rotate-180" : ""}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute top-full left-0 mt-1.5 w-52 rounded-md border border-border overflow-hidden shadow-lg z-50"
          style={{ background: "var(--color-surface-raised, var(--color-surface-card))" }}
        >
          {products.map((p) => {
            const active = p.slug === currentSlug;
            return (
              <button
                key={p.slug}
                onClick={() => switchTo(p.slug)}
                className="w-full flex items-center justify-between px-3 py-2 text-sm text-left transition-colors hover:bg-muted/60"
                style={{ color: active ? "var(--color-foreground)" : "var(--color-ink-dim)" }}
              >
                <span className="truncate">{p.name}</span>
                {active && (
                  <svg
                    width="12" height="12" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                    className="shrink-0 ml-2"
                    style={{ color: "var(--color-signal)" }}
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
