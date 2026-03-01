# UI Redesign: Modern SaaS Dashboard

**Date:** 2026-03-01
**Status:** Approved
**Branch:** ui-work

## Goal

Replace the current Streamlit-parity frontend with a modern SaaS dashboard (Linear/Vercel aesthetic) using PrimeVue components properly — proper icon system, design tokens, accordion cards, dark sidebar, and colored KPI tiles.

## What Changes vs. What Stays

**Unchanged:**
- `src/stores/` — Pinia stores (insights, reviews)
- `src/api/client.ts` — Axios API client
- `src/types/index.ts` — TypeScript types

**Replaced entirely:**
- `src/theme/wealthsimple.ts` — comprehensive PrimeVue preset with semantic tokens
- `src/components/KpiTiles.vue` — colored stat cards with PrimeIcons
- `src/components/InsightCard.vue` — accordion card (collapsed by default)
- `src/components/FilterSidebar.vue` — dark sidebar with SelectButton/ToggleButton groups
- `src/components/TopicsChart.vue` — reskinned chart colors
- `src/views/Dashboard.vue` — new layout shell
- `src/App.vue` — root layout adjustments

## Layout

```
┌──────────────────────────────────────────────────────┐
│ SIDEBAR (240px)         │  MAIN CONTENT              │
│ dark navy #1C2333       │  bg: #F8F9FB               │
│                         │                            │
│  ● WS Intelligence      │  Community Intelligence    │
│                         │  AI finds signal. You build│
│  Filters                │                            │
│  ─────────              │  ┌──┐ ┌──┐ ┌──┐ ┌──┐      │
│  Category               │  │KPI│ │KPI│ │KPI│ │KPI│  │
│  ○ All  ○ Roadmap       │  └──┘ └──┘ └──┘ └──┘      │
│  ○ Friction  ○ Win      │                            │
│                         │  ── Bar chart ─────────    │
│  Confidence             │                            │
│  ○ All  ○ High          │  Insight Cards (accordion) │
│  ○ Med  ○ Low           │  ┌──────────────────────┐  │
│                         │  │ 🗺 Roadmap  HIGH  ··· │  │
│  Status                 │  │ Headline text         │  │
│  ○ Pending only         │  └──────────────────────┘  │
│  ○ Flagged              │  ┌──────────────────────┐  │
│                         │  │ 🔥 Friction  MED  ··· │  │
└──────────────────────────────────────────────────────┘
```

## Components

### KpiTiles
- 4 cards in a horizontal row (CSS grid, 4 cols)
- Each card: colored left-border accent + PrimeIcons icon + large number + label
- Color semantics: amber (pending), red (flagged), teal (total posts), blue (total insights)
- Subtle `box-shadow` lift on hover with 150ms transition

### InsightCard (Accordion)
- Uses PrimeVue `Accordion` + `AccordionPanel`
- **Collapsed header**: category icon (PrimeIcons) + category badge + confidence Tag + post count + headline + "⚠ Needs Review" chip if flagged
- **Expanded body**: summary, evidence blockquotes, product action, Canadian context pill, review controls (Select + Textarea + Save button)
- Collapse/expand animation via PrimeVue built-in

### FilterSidebar
- Dark navy background (`#1C2333`), light text (`#94A3B8`), active state mint green (`#00C4A0`)
- Category: `SelectButton` (All / Roadmap / Friction / Win / Other)
- Confidence: `SelectButton` (All / High / Medium / Low)
- Status: `ToggleButton` for "Pending only" and "Flagged for review"
- Filter state wired to existing Pinia store filters

### TopicsChart
- Chart.js colors updated to match theme palette
- Bar color: `#00C4A0` with opacity variants

## Theme Tokens

```typescript
// Primary: Wealthsimple mint
primary: { 500: '#00C4A0', 400: '#33CDB3', 600: '#00A887' }

// Surface ramp (light mode)
surface: {
  0: '#FFFFFF', 50: '#F8F9FB', 100: '#F1F3F6',
  200: '#E2E8F0', 300: '#CBD5E1', 400: '#94A3B8',
  500: '#64748B', 600: '#475569', 700: '#334155',
  800: '#1E293B', 900: '#0F172A'
}

// Status accent colors (KPI tiles, used via CSS vars)
--color-pending: #F59E0B
--color-flagged: #EF4444
--color-posts:   #00C4A0
--color-insights: #3B82F6
```

## Transitions & Polish
- All hover states: `transition: all 150ms ease`
- Card expand/collapse: PrimeVue Accordion built-in animation
- KPI cards: `box-shadow` lift on hover
- Sidebar active items: left border highlight in mint green

## Out of Scope
- Dark mode toggle
- Mobile/responsive layout
- Pagination or virtual scrolling
- Real-time updates
