"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  discoverSources,
  createProduct,
  type DiscoveredSource,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function slugify(text: string) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_]+/g, "-");
}

const SOURCE_LABELS: Record<string, string> = {
  google_play:    "Google Play",
  apple_app_store: "App Store",
  reddit:         "Reddit",
  youtube:        "YouTube",
};

// ---------------------------------------------------------------------------
// Spinner
// ---------------------------------------------------------------------------

function Spinner() {
  return (
    <svg
      className="animate-spin"
      width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2"
      style={{ color: "var(--color-signal)" }}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Step 1 — Discovery
// ---------------------------------------------------------------------------

interface DiscoverStepProps {
  onDone: (sources: DiscoveredSource[], keywords: string[], name: string, country: string) => void;
  onCancel: () => void;
}

function DiscoverStep({ onDone, onCancel }: DiscoverStepProps) {
  const [name, setName] = useState("");
  const [country, setCountry] = useState("us");
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  async function handleDiscover() {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    setPhase("Searching app stores…");

    // Staggered phase labels so the user knows what's happening
    const phaseTimer = setTimeout(() => setPhase("Asking Gemini for communities…"), 2500);
    try {
      const result = await discoverSources(name.trim(), country);
      clearTimeout(phaseTimer);
      onDone(result.sources, result.keywords, name.trim(), country);
    } catch (e) {
      clearTimeout(phaseTimer);
      setError((e as Error).message || "Discovery failed.");
    } finally {
      setLoading(false);
      setPhase(null);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs text-muted-foreground mb-3">
          Enter a product name and we'll search Google Play, App Store, Reddit, and YouTube for relevant sources.
        </p>
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleDiscover()}
            placeholder="e.g. Mintlify"
            className="flex-1 h-9 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary"
          />
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="us">🇺🇸 US</option>
            <option value="ca">🇨🇦 CA</option>
            <option value="gb">🇬🇧 GB</option>
            <option value="au">🇦🇺 AU</option>
            <option value="in">🇮🇳 IN</option>
          </select>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
          <Spinner />
          <span>{phase}</span>
        </div>
      )}

      {error && (
        <p className="text-sm" style={{ color: "var(--color-negative)" }}>{error}</p>
      )}

      <div className="flex justify-end gap-2">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleDiscover}
          disabled={loading || !name.trim()}
          className="px-4 py-1.5 text-sm rounded-md bg-primary text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-40"
        >
          {loading ? "Discovering…" : "Discover sources"}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2 — Review & create
// ---------------------------------------------------------------------------

interface ReviewStepProps {
  sources: DiscoveredSource[];
  suggestedKeywords: string[];
  initialName: string;
  country: string;
  onBack: () => void;
  onCancel: () => void;
}

function ReviewStep({ sources, suggestedKeywords, initialName, country, onBack, onCancel }: ReviewStepProps) {
  const router = useRouter();

  // Source selection — pre-check "confirmed" sources
  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(sources.filter((s) => s.confidence === "confirmed").map((s) => s.source_ref))
  );

  const [name, setName] = useState(initialName);
  const [slug, setSlug] = useState(slugify(initialName));
  const [description, setDescription] = useState("");
  const [keywords, setKeywords] = useState(suggestedKeywords.join(", "));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Keep slug in sync while user edits name (until they manually touch slug)
  const slugTouched = useRef(false);
  function handleNameChange(v: string) {
    setName(v);
    if (!slugTouched.current) setSlug(slugify(v));
  }

  function toggleSource(ref: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(ref) ? next.delete(ref) : next.add(ref);
      return next;
    });
  }

  async function handleCreate() {
    if (!name.trim() || !slug.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const chosenSources = sources
        .filter((s) => selected.has(s.source_ref))
        .map((s) => ({ source_type: s.source_type, source_ref: s.source_ref }));

      const kws = keywords.split(",").map((k) => k.trim()).filter(Boolean);

      const product = await createProduct({
        name: name.trim(),
        slug: slug.trim(),
        description: description.trim(),
        keywords: kws,
        sources: chosenSources,
      });

      router.push(`/products/${product.slug}/dashboard`);
    } catch (e) {
      setError((e as Error).message || "Failed to create product.");
      setSaving(false);
    }
  }

  // Group sources by type for display
  const byType = sources.reduce<Record<string, DiscoveredSource[]>>((acc, s) => {
    (acc[s.source_type] ??= []).push(s);
    return acc;
  }, {});

  const TYPE_ORDER = ["google_play", "apple_app_store", "reddit", "youtube"];

  return (
    <div className="space-y-5">
      {/* Source picker */}
      <div>
        <p className="text-xs text-muted-foreground mb-2">Select sources to monitor</p>
        <div className="rounded-md border border-border overflow-hidden divide-y divide-border">
          {TYPE_ORDER.filter((t) => byType[t]?.length).map((type) => (
            <div key={type}>
              <p className="px-3 py-1.5 text-[10px] uppercase tracking-wide text-muted-foreground"
                style={{ background: "var(--color-surface-base)" }}>
                {SOURCE_LABELS[type]}
              </p>
              {byType[type].map((s) => (
                <label
                  key={s.source_ref}
                  className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-muted/40 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(s.source_ref)}
                    onChange={() => toggleSource(s.source_ref)}
                    className="accent-primary"
                  />
                  <span className="text-sm flex-1">{s.display}</span>
                  <span
                    className="text-[10px]"
                    style={{ color: s.confidence === "confirmed" ? "var(--color-positive)" : "var(--color-ink-dim)" }}
                  >
                    {s.confidence}
                  </span>
                </label>
              ))}
            </div>
          ))}
          {sources.length === 0 && (
            <p className="px-3 py-4 text-sm text-center text-muted-foreground">
              No sources found — you can add them later in Settings.
            </p>
          )}
        </div>
      </div>

      {/* Product details */}
      <div className="space-y-3">
        <p className="text-xs text-muted-foreground">Product details</p>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <label className="text-[10px] text-muted-foreground uppercase tracking-wide">Name</label>
            <input
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="w-full h-8 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] text-muted-foreground uppercase tracking-wide">Slug</label>
            <input
              value={slug}
              onChange={(e) => { slugTouched.current = true; setSlug(e.target.value); }}
              className="w-full h-8 rounded-md border border-input bg-background px-3 text-sm font-mono outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-[10px] text-muted-foreground uppercase tracking-wide">Description</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional"
            className="w-full h-8 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <div className="space-y-1">
          <label className="text-[10px] text-muted-foreground uppercase tracking-wide">Keywords (comma-separated)</label>
          <input
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            className="w-full h-8 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      {error && (
        <p className="text-sm" style={{ color: "var(--color-negative)" }}>{error}</p>
      )}

      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          ← Back
        </button>
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={saving || !name.trim() || !slug.trim()}
            className="flex items-center gap-2 px-4 py-1.5 text-sm rounded-md bg-primary text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-40"
          >
            {saving && <Spinner />}
            {saving ? "Creating…" : `Create${selected.size > 0 ? ` with ${selected.size} source${selected.size > 1 ? "s" : ""}` : ""}`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Modal shell
// ---------------------------------------------------------------------------

interface AddProductModalProps {
  onClose: () => void;
}

export function AddProductModal({ onClose }: AddProductModalProps) {
  const [step, setStep] = useState<"discover" | "review">("discover");
  const [discovered, setDiscovered] = useState<DiscoveredSource[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [productName, setProductName] = useState("");
  const [country, setCountry] = useState("us");
  const overlayRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") onClose(); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function handleDiscoverDone(sources: DiscoveredSource[], kws: string[], name: string, ctry: string) {
    setDiscovered(sources);
    setKeywords(kws);
    setProductName(name);
    setCountry(ctry);
    setStep("review");
  }

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh] px-4"
      style={{ background: "rgba(0,0,0,0.55)" }}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div
        className="w-full max-w-lg rounded-lg border border-border shadow-2xl overflow-hidden"
        style={{ background: "var(--color-surface-card)" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="text-sm font-semibold">New product</h2>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {step === "discover" ? "Step 1 of 2 — Discover sources" : "Step 2 of 2 — Review & create"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-5">
          {step === "discover" ? (
            <DiscoverStep
              onDone={handleDiscoverDone}
              onCancel={onClose}
            />
          ) : (
            <ReviewStep
              sources={discovered}
              suggestedKeywords={keywords}
              initialName={productName}
              country={country}
              onBack={() => setStep("discover")}
              onCancel={onClose}
            />
          )}
        </div>
      </div>
    </div>
  );
}
