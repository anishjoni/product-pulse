# Product Pulse — Interface System

## Direction

Dark monitoring interface. Deep slate surfaces. Electric indigo signal accent. The PM opens it, reads it, closes it knowing what's happening with their product. Feels like a calibrated control room — dense, readable, purposeful.

**Who:** Product manager between meetings. Scanning community health. Needs to act, not admire.
**What:** Identify what's rising, catch problems early, understand feedback mix.
**Feel:** Vercel analytics crossed with a Bloomberg terminal. Professional. No decoration.

---

## Token System

Defined in `frontend/src/app/globals.css`. Shadcn token names kept for component compatibility — values replaced with dark slate theme.

### Surfaces (elevation via lightness only, no shadows)
| Token | HSL | Hex | Use |
|---|---|---|---|
| `--background` | `220 14% 7%` | `#0D1117` | Base canvas |
| `--card` | `215 18% 11%` | `#161B22` | Cards, panels |
| `--popover` | `220 28% 16%` | `#1C2333` | Dropdowns, tooltips, raised |
| `--muted` | `215 18% 14%` | — | Subtle backgrounds |

### Text
| Token | HSL | Hex | Use |
|---|---|---|---|
| `--foreground` | `210 40% 96%` | `#E6EDF3` | Primary text |
| `--muted-foreground` | `213 9% 57%` | `#8B949E` | Secondary/supporting |
| `--ink-faint` (hex var) | — | `#484F58` | Metadata, disabled |

### Signal & Semantic
| Token | Hex | Use |
|---|---|---|
| `--primary` / `--color-signal` | `#6366F1` | Electric indigo — primary actions, key highlights only |
| `--color-positive` | `#10B981` | Good news, success |
| `--color-negative` / `--destructive` | `#EF4444` | Errors, bugs, problems |
| `--color-warning` | `#F59E0B` | Caution, low confidence |

### Borders
| Token | Hex | Use |
|---|---|---|
| `--border` / `--color-wire` | `#21262D` | Standard separation |
| `--color-wire-strong` | `#30363D` | Emphasis, hover states |

### Hex vars (for Recharts + inline styles)
All defined as `--color-*` CSS variables on `:root`. Use these wherever `hsl(var(--x))` won't work:
`--color-signal`, `--color-positive`, `--color-negative`, `--color-warning`, `--color-ink`, `--color-ink-dim`, `--color-ink-faint`, `--color-wire`, `--color-wire-strong`, `--color-surface-base`, `--color-surface-card`, `--color-surface-raised`

---

## Depth Strategy

**Surface color shifts only. No box-shadows.**

- Elevation is communicated purely by lightness: base → card → raised
- Wire borders (`border-border`) for structural separation
- Hover: `border-muted-foreground/30` or `--color-wire-strong`
- Focus: `ring-1 ring-ring` (signal color)
- Never mix shadows and surface shifts

---

## Typography

Geist Sans + Geist Mono loaded as local fonts via `--font-geist-sans` and `--font-geist-mono`.

- **Data values** (counts, percentages, scores): `font-family: var(--font-geist-mono)`, `tabular-nums`
- **Labels**: `text-[10px] uppercase tracking-wide text-muted-foreground`
- **Body**: `text-sm` default
- **Headlines**: `text-lg font-semibold` max — no large display type

---

## Spacing

Base unit: 4px (Tailwind default). Standard component padding: `p-3` or `p-4`. Section gaps: `space-y-5` or `gap-5`.

---

## Border Radius

`--radius: 0.375rem`. Inputs/buttons: `rounded` (sm). Cards/containers: `rounded` (same). No large radius anywhere — this is a technical tool, not a consumer app.

---

## Category Color System

Defined in `frontend/src/lib/utils.ts`. These are semantic identity colors — do not replace with theme tokens.

```ts
feature_request: "#3B82F6"  // blue
bug_report:      "#EF4444"  // red
complaint:       "#F97316"  // orange
praise:          "#22C55E"  // green
general_discussion: "#6B7280"  // gray
```

**Usage pattern:** Category color appears as a 3px left border stripe on cards/items — never as a filled background. Exception: PulseScoreBar segments use full background fill.

---

## Component Patterns

### Navigation (NavLinks)
- Client component (`components/NavLinks.tsx`) — uses `usePathname` for active detection
- Active: `text-foreground bg-muted` pill
- Inactive: `text-muted-foreground hover:text-foreground hover:bg-muted/60`
- Header: 48px (`h-12`), `border-b border-border`, same bg as content

### PulseScoreBar (Vitals Strip Hero)
- **60px tall** — the signature element, the EKG of the product community
- Segments: full-color background, white label + monospace count when segment ≥ 12% wide
- Selected: `opacity: 1` + bottom 3px white/50 indicator
- Non-selected when something selected: `opacity: 0.4`
- Click selected → deselect (pass `null`)
- Props: `counts`, `selectedCategory`, `onCategoryClick: (cat: string | null) => void`

### CategoryCards
- Grid: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2`
- Structure: left 3px color stripe + content column
- Content: `text-[10px] uppercase tracking-wide` label → `text-[22px] font-bold tabular-nums font-mono` count → `text-[10px] text-muted-foreground` percentage
- Selected: `borderColor: catColor, boxShadow: 0 0 0 1px catColor`
- Background: `bg-card border border-border rounded`

### FeedCard
- Container: `bg-card border border-border rounded overflow-hidden`
- Hover: `hover:border-muted-foreground/30`
- Left stripe (3px, category color) + content column
- Meta row: category label in category color, source in `text-muted-foreground uppercase tracking-wide`
- Summary: dominant `text-sm` element
- Sentiment dot: 6px rounded-full in semantic color
- "View original" link: `--color-signal`
- Raw expanded: `bg-[var(--color-surface-base)] border border-border`

### Chart Containers (Dashboard)
- Wrapper: `rounded bg-card border border-border p-4`
- Label: `text-xs text-muted-foreground mb-3`
- No section headers

### Recharts Color Constants
Use this pattern in all chart files — Recharts renders SVG and cannot read CSS vars:
```ts
const C = {
  grid:          "#21262D",
  tick:          "#484F58",
  zero:          "#30363D",
  signal:        "#6366F1",
  tooltipBg:     "#1C2333",
  tooltipBorder: "#30363D",
  tooltipText:   "#E6EDF3",
  label:         "#8B949E",
};
```
Tooltip: custom component, `rounded px-3 py-2 text-xs`, background/border from `C`.

### Status Chips
```tsx
const styles =
  status === "completed" ? "bg-[#10B981]/15 text-[#10B981]"
  : status === "running"  ? "bg-[#F59E0B]/15 text-[#F59E0B]"
  :                         "bg-[#EF4444]/15 text-[#EF4444]";
// text-[10px] font-medium px-1.5 py-0.5 rounded
```

### FeedFilters Category Pills
- Default: `border: --color-wire, color: --color-ink-dim`
- Active: `border: catColor, color: catColor, background: catColor + "18"` (10% opacity)
- Color dot (6px) inside each pill

---

## Always Dark

`<html lang="en" className="dark">` in root layout. No light mode toggle. No `dark:` variants needed in component code.
