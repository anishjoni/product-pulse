"use client";

import { useEffect, useState } from "react";
import { getProducts, updateProduct, type Product } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

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
    if (kw && !keywords.includes(kw)) {
      setKeywords((prev) => [...prev, kw]);
    }
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

  if (!product) return <p className="p-8 text-muted-foreground">Loading…</p>;

  return (
    <main className="p-6 max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Settings — {product.name}</h1>

      {/* Keywords */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Keywords</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {keywords.map((kw) => (
              <Badge
                key={kw}
                variant="secondary"
                className="cursor-pointer"
                onClick={() => removeKeyword(kw)}
                title="Click to remove"
              >
                {kw} ×
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              placeholder="Add keyword…"
              onKeyDown={(e) => e.key === "Enter" && addKeyword()}
            />
            <Button variant="outline" onClick={addKeyword}>
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Sources */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Sources</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {sources.map((s, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <Badge variant="outline" className="capitalize">
                {s.source_type}
              </Badge>
              <span className="flex-1 font-mono text-xs">{s.source_ref}</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-muted-foreground"
                onClick={() => removeSource(i)}
              >
                ×
              </Button>
            </div>
          ))}
          <div className="flex gap-2">
            <select
              value={newSourceType}
              onChange={(e) => setNewSourceType(e.target.value)}
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="reddit">Reddit</option>
              <option value="youtube">YouTube</option>
              <option value="google_play">Google Play</option>
              <option value="apple_app_store">App Store</option>
            </select>
            <Input
              value={newSourceRef}
              onChange={(e) => setNewSourceRef(e.target.value)}
              placeholder={
                newSourceType === "reddit" ? "subreddit name (e.g. wealthsimple)" :
                newSourceType === "youtube" ? "search term (e.g. wealthsimple review)" :
                newSourceType === "google_play" ? "com.example.app:ca" :
                "1234567890:us"
              }
              onKeyDown={(e) => e.key === "Enter" && addSource()}
            />
            <Button variant="outline" onClick={addSource}>
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save Changes"}
        </Button>
        {saved && <span className="text-green-600 text-sm">Saved!</span>}
      </div>

      <Separator />
      <div className="text-xs text-muted-foreground space-y-1">
        <p>Scout schedule: configured via <code>SCOUT_SCHEDULE_CRON</code> env var (default: daily 06:00 UTC)</p>
        <p>Product slug: <code>{product.slug}</code></p>
      </div>
    </main>
  );
}
