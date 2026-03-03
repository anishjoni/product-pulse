# Phase 6 — Frontend Dashboard

## Goal
A clean, data-dense internal dashboard built with Next.js 14 + Shadcn/UI + Recharts.
Mobile responsive. No login screen for the demo — just an API key header (handled by
the API layer, not the frontend).

## Agents Involved
- Frontend (implementation)
- QA (validate all pages load, filters work, data is correctly displayed)

## Pages & Routes

### `/` → Product selector
If only one product exists, redirect straight to `/products/[slug]/dashboard`.
If multiple products, show a simple card grid to pick one.

### `/products/[slug]/dashboard` → Pulse Overview
The main screen. Composed of:

**Header Strip**
- Product name + last scout time ("Last updated 2 hours ago")
- "Run Scout Now" button → calls `POST /products/{id}/scout`, shows loading state
- Scout status badge (green = completed, yellow = running, red = failed)

**Pulse Score Bar** (top of page)
- 5 horizontal segments, one per category, width proportional to count
- Color coding:
  - feature_request: blue (#3B82F6)
  - bug_report: red (#EF4444)
  - complaint: orange (#F97316)
  - praise: green (#22C55E)
  - general_discussion: gray (#6B7280)
- Hovering a segment shows count + % of total

**Category Cards Row** (5 cards)
- One card per category
- Shows: count, % of total, delta vs previous period (↑↓ with arrow)
- Clicking a card filters the feedback feed below to that category

**Trending Topics Bar Chart** (Recharts horizontal bar chart)
- X axis: mention count (current window)
- Y axis: topic labels
- Bar fill: gradient from gray to blue based on pct_change intensity
- Tooltip: shows current_count, previous_count, pct_change, category_breakdown
- Top 10 trends only, sorted by pct_change DESC
- Label on bar: "+200%" pct_change annotation

**Sentiment Timeline** (Recharts line chart)
- X axis: date (last 14 days)
- Y axis: average sentiment (-1 to 1)
- Line color changes: green above 0, red below 0
- One data point per day

### `/products/[slug]/feed` → Feedback Feed

**Filters Bar** (sticky top)
- Category multi-select (pills/chips, default: all)
- Source toggle: Reddit | YouTube | All
- Sentiment: All | Positive | Neutral | Negative
- Date range picker
- Search input (debounced 300ms, calls API search param)

**Feed** (infinite scroll or pagination)
Each card shows:
- Category badge (color-coded, same palette as above)
- Source badge (Reddit / YouTube) + subreddit or channel name
- LLM summary (one sentence, prominent)
- Sentiment indicator (colored dot + score)
- Confidence badge (only shown if < 0.7 — flags low-confidence classifications)
- Date ("3 hours ago")
- "View original" link → opens source URL in new tab
- Expandable section: shows full raw content on click

### `/products/[slug]/trends` → Trends Deep-dive
- Full trends table: topic | current count | previous count | % change | top category
- Click a topic row → shows all feedback items mentioning that topic (filtered feed)
- Export button → downloads trends as CSV

### `/products/[slug]/settings` → Product Settings
- Edit product name and description
- Manage keywords (add/remove chips)
- Manage sources: toggle Reddit subreddits on/off, add new subreddits, YouTube terms
- Scout schedule display (read-only for demo)

## Component Structure
```
src/
  app/
    page.tsx                        # product selector
    products/
      [slug]/
        dashboard/page.tsx
        feed/page.tsx
        trends/page.tsx
        settings/page.tsx
  components/
    pulse/
      PulseScoreBar.tsx
      CategoryCards.tsx
      TrendingBarChart.tsx
      SentimentTimeline.tsx
    feed/
      FeedCard.tsx
      FeedFilters.tsx
    ui/                             # Shadcn components (auto-generated)
  lib/
    api.ts                          # typed API client (fetch wrappers for all endpoints)
    utils.ts
```

## Design Constraints
- Use Shadcn/UI for all form elements, cards, badges, dialogs
- Use Recharts for all charts (already works with Next.js, no SSR issues)
- Tailwind CSS for layout — no custom CSS files
- Dark mode: support it via Shadcn's built-in theme toggle (optional for demo)
- No authentication UI — the demo assumes it's running on an internal network

## API Client (lib/api.ts)
Typed wrappers around every endpoint. Example:
```typescript
export async function getProductSummary(productId: number): Promise<ProductSummary> {
  const res = await fetch(`${API_BASE}/products/${productId}/summary`)
  if (!res.ok) throw new Error(`Failed to fetch summary: ${res.status}`)
  return res.json()
}
```

## Environment Variables
```
NEXT_PUBLIC_API_BASE=http://localhost:8000   # or Modal URL in prod
```

## Acceptance Criteria
- [ ] Dashboard loads with correct category counts for seeded data
- [ ] Pulse Score Bar segments are proportionally sized and color-coded
- [ ] Clicking a category card filters the feed to that category
- [ ] Trending bar chart renders with correct topic labels and pct_change
- [ ] Feed shows LLM summary (not raw Reddit text) by default
- [ ] "View original" opens the correct Reddit/YouTube URL
- [ ] Expanding a feed card shows full raw content
- [ ] Feed filters (category, source, sentiment) all correctly filter results
- [ ] "Run Scout Now" button triggers scout and shows a loading/progress state
- [ ] Settings page saves updated keywords and sources via API
- [ ] App is usable on a 375px mobile screen (no horizontal scroll)
