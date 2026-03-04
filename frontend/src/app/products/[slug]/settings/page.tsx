"use client";

import { useEffect, useState } from "react";
import { getProducts, updateProduct, type Product } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function SettingsPage({ params }: { params: { slug: string } }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [sources, setSources] = useState<{ source_type: string; source_ref: string }[]>([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [newSourceType, setNewSourceType] = useState("reddit");
  const [newSourceRef, setNewSourceRef] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getProducts().then((ps) => {
      const p = ps.find((x) => x.slug === params.slug);
      if (!p) return;
      setProduct(p);
      setKeywords(p.keywords);
      setSources(p.sources.map((s) => ({ source_type: s.source_type, source_ref: s.source_ref })));
    });
  }, [params.slug]);

  function addKeyword() {
    const kw = newKeyword.trim();
    if (kw && !keywords.includes(kw)) setKeywords((prev) => [...prev, kw]);
    setNewKeyword("");
  }

  function removeKeyword(kw: string) {
    setKeywords((prev) => prev.filter((k) => k !== kw));
  }

  function addSource() {
    const ref = newSourceRef.trim();
    if (ref) {
      setSources((prev) => [...prev, { source_type: newSourceType, source_ref: ref }]);
      setNewSourceRef("");
    }
  }

  function removeSource(idx: number) {
    setSources((prev) => prev.filter((_, i) => i !== idx));
  }

  async function handleSave() {
    if (!product) return;
    setSaving(true);
    try {
      await updateProduct(product.id, { keywords, sources });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  if (!product) return (
    <p className="p-8 font-mono text-[10px] tracking-widest uppercase text-muted-foreground animate-pulse">
      LOADING…
    </p>
  );

  return (
    <main className="p-6 max-w-2xl mx-auto space-y-6">
      <div className="pb-4 border-b border-border">
        <h1 className="font-display font-bold text-xl tracking-tight text-foreground">
          Settings
        </h1>
        <p className="font-mono text-[10px] text-muted-foreground tracking-widest mt-1">
          {product.name.toUpperCase()} · SLUG: {product.slug}
        </p>
      </div>

      {/* Keywords */}
      <section className="space-y-3">
        <p className="font-display text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground">
          Keywords
        </p>
        <div className="border border-border rounded-sm p-4 space-y-3 bg-card">
          <div className="flex flex-wrap gap-2">
            {keywords.map((kw) => (
              <button
                key={kw}
                type="button"
                role="button"
                tabIndex={0}
                aria-label={`Remove keyword ${kw}`}
                className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-widest uppercase px-2 py-0.5 rounded-sm bg-background border border-border text-muted-foreground hover:text-destructive hover:border-destructive/50 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                onClick={() => removeKeyword(kw)}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && removeKeyword(kw)}
              >
                {kw}
                <span className="text-[10px] leading-none">×</span>
              </button>
            ))}
            {keywords.length === 0 && (
              <p className="font-mono text-[10px] tracking-widest text-muted-foreground/50">
                No keywords yet.
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <Input
              aria-label="New keyword"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              placeholder="Add keyword…"
              onKeyDown={(e) => e.key === "Enter" && addKeyword()}
              className="h-8 font-mono text-xs border-border bg-background"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={addKeyword}
              className="h-8 px-3 font-mono text-[10px] tracking-widest uppercase border border-border text-muted-foreground hover:text-foreground"
            >
              ADD
            </Button>
          </div>
        </div>
      </section>

      {/* Sources */}
      <section className="space-y-3">
        <p className="font-display text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground">
          Sources
        </p>
        <div className="border border-border rounded-sm overflow-hidden bg-card">
          {sources.map((s, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2.5 border-b border-border last:border-b-0">
              <span className="font-mono text-[10px] tracking-widest uppercase text-primary shrink-0">
                {s.source_type}
              </span>
              <span className="flex-1 min-w-0 font-mono text-xs text-muted-foreground truncate">
                {s.source_ref}
              </span>
              <Button
                variant="ghost"
                size="sm"
                aria-label={`Remove ${s.source_type} source ${s.source_ref}`}
                className="h-6 px-2 font-mono text-[10px] text-muted-foreground hover:text-destructive shrink-0"
                onClick={() => removeSource(i)}
              >
                ×
              </Button>
            </div>
          ))}
          {sources.length === 0 && (
            <p className="px-4 py-3 font-mono text-[10px] tracking-widest text-muted-foreground/50">
              No sources yet.
            </p>
          )}
          <div className="flex gap-2 p-3 border-t border-border bg-background">
            <select
              aria-label="Source type"
              value={newSourceType}
              onChange={(e) => setNewSourceType(e.target.value)}
              className="h-8 rounded-sm border border-border bg-card px-2 font-mono text-[10px] tracking-widest uppercase text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="reddit">REDDIT</option>
              <option value="youtube">YOUTUBE</option>
              <option value="google_play">GOOGLE PLAY</option>
              <option value="apple_app_store">APP STORE</option>
            </select>
            <Input
              aria-label="Source reference"
              value={newSourceRef}
              onChange={(e) => setNewSourceRef(e.target.value)}
              placeholder={
                newSourceType === "reddit" ? "subreddit (e.g. wealthsimple)" :
                newSourceType === "youtube" ? "search term (e.g. wealthsimple review)" :
                newSourceType === "google_play" ? "com.example.app:ca" :
                "1234567890:us"
              }
              onKeyDown={(e) => e.key === "Enter" && addSource()}
              className="h-8 font-mono text-xs border-border bg-card flex-1"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={addSource}
              className="h-8 px-3 font-mono text-[10px] tracking-widest uppercase border border-border text-muted-foreground hover:text-foreground"
            >
              ADD
            </Button>
          </div>
        </div>
      </section>

      <div className="flex items-center gap-3 pt-2">
        <Button
          onClick={handleSave}
          disabled={saving}
          size="sm"
          className="font-display font-semibold text-[11px] tracking-[0.12em] uppercase"
        >
          {saving ? "Saving…" : "Save Changes"}
        </Button>
        {saved && (
          <span className="font-mono text-[10px] tracking-widest uppercase text-[#3fb950]">
            SAVED ✓
          </span>
        )}
      </div>

      <div className="border-t border-border pt-4 space-y-1">
        <p className="font-mono text-[10px] text-muted-foreground/60">
          Scout schedule: <code className="text-muted-foreground">SCOUT_SCHEDULE_CRON</code> env var (default: daily 06:00 UTC)
        </p>
      </div>
    </main>
  );
}
