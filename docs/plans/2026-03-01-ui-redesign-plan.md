# UI Redesign: Modern SaaS Dashboard — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Rebuild the WS Intelligence frontend with a modern SaaS dashboard aesthetic — dark navy sidebar, colored KPI tiles with PrimeIcons, accordion insight cards, and PrimeVue components used properly throughout.

**Architecture:** Replace all 4 Vue components + Dashboard view. Stores (`src/stores/`), types (`src/types/`), and API client (`src/api/`) are untouched. No new npm dependencies — PrimeIcons 7 is already installed.

**Tech Stack:** Vue 3, TypeScript 5.9, PrimeVue 4.5, PrimeIcons 7, Chart.js 4

**Build verification:** `bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run build'`

---

### Task 1: Rebuild KpiTiles.vue

**Files:**
- Modify: `frontend/src/components/KpiTiles.vue`

Adds colored left-border accent, PrimeIcons icon in a tinted circle, and hover lift. No new imports needed — PrimeIcons is already in `node_modules/primeicons/`.

**Step 1: Replace the file**

```vue
<template>
  <div class="kpi-row">
    <div
      v-for="tile in tiles"
      :key="tile.label"
      class="kpi-card"
      :style="{ '--accent': tile.color }"
    >
      <div class="kpi-icon-wrap">
        <i :class="['pi', tile.icon]" />
      </div>
      <div class="kpi-body">
        <span class="kpi-value">{{ tile.value }}</span>
        <span class="kpi-label">{{ tile.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Stats } from '@/types'

const props = defineProps<{ stats: Stats }>()

const tiles = computed(() => [
  { label: 'Posts analyzed', value: props.stats.total_posts.toLocaleString(), icon: 'pi-comments',             color: '#00C4A0' },
  { label: 'Insight cards',  value: props.stats.total_insights,               icon: 'pi-lightbulb',            color: '#3B82F6' },
  { label: 'Pending review', value: props.stats.pending_review,               icon: 'pi-clock',                color: '#F59E0B' },
  { label: 'Flagged',        value: props.stats.flagged_for_review,           icon: 'pi-exclamation-triangle', color: '#EF4444' },
])
</script>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.kpi-card {
  background: var(--p-surface-0);
  border: 1px solid var(--p-surface-200);
  border-left: 4px solid var(--accent);
  border-radius: 10px;
  padding: 1.125rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: box-shadow 150ms ease, transform 150ms ease;
}
.kpi-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}
.kpi-icon-wrap {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 8px;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kpi-icon-wrap .pi {
  font-size: 1.125rem;
  color: var(--accent);
}
.kpi-body {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.kpi-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--p-surface-900);
  line-height: 1;
}
.kpi-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--p-surface-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
```

**Step 2: Verify build passes**

Run: `bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run build 2>&1 | tail -20'`

Expected: `✓ built in` with no TypeScript errors.

**Step 3: Commit**

```bash
cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work
git add frontend/src/components/KpiTiles.vue
git commit -m "feat: rebuild KpiTiles with colored accents and PrimeIcons"
```

---

### Task 2: Rebuild FilterSidebar.vue

**Files:**
- Modify: `frontend/src/components/FilterSidebar.vue`

Replaces Checkbox + ProgressBar with SelectButton (for category/confidence) and ToggleButton (for flagged filter). Deep CSS overrides make PrimeVue controls look correct on the dark navy sidebar background that Dashboard.vue provides.

The store's `filters` object (`insightsStore.filters`) contains:
- `categories: Category[]` — array of selected category strings
- `confidences: Confidence[]` — array of selected confidence strings
- `flaggedOnly: boolean`

SelectButton with `multiple` binds directly to these arrays.

**Step 1: Replace the file**

```vue
<template>
  <div class="filter-sidebar">
    <div class="filter-section">
      <p class="section-label">Category</p>
      <SelectButton
        v-model="filters.categories"
        :options="CATEGORIES"
        optionLabel="label"
        optionValue="value"
        multiple
        class="filter-select"
      />
    </div>

    <div class="filter-section">
      <p class="section-label">Confidence</p>
      <SelectButton
        v-model="filters.confidences"
        :options="CONFIDENCES"
        optionLabel="label"
        optionValue="value"
        multiple
        class="filter-select"
      />
    </div>

    <div class="filter-section">
      <ToggleButton
        v-model="filters.flaggedOnly"
        onLabel="Flagged only"
        offLabel="Flagged only"
        onIcon="pi pi-exclamation-triangle"
        offIcon="pi pi-exclamation-triangle"
        class="filter-toggle"
      />
    </div>

    <div class="filter-section">
      <p class="section-label">Review progress</p>
      <div class="progress-wrap">
        <div class="progress-fill" :style="{ width: progressPct + '%' }" />
      </div>
      <p class="progress-text">{{ reviewedCount }} / {{ totalCount }} reviewed</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SelectButton from 'primevue/selectbutton'
import ToggleButton from 'primevue/togglebutton'
import { useInsightsStore } from '@/stores/insights'
import { useReviewsStore } from '@/stores/reviews'

const insightsStore = useInsightsStore()
const reviewsStore = useReviewsStore()
const filters = insightsStore.filters

const CATEGORIES = [
  { value: 'roadmap',  label: 'Roadmap' },
  { value: 'friction', label: 'Friction' },
  { value: 'win',      label: 'Win' },
  { value: 'other',    label: 'Other' },
]
const CONFIDENCES = [
  { value: 'high',   label: 'High' },
  { value: 'medium', label: 'Med' },
  { value: 'low',    label: 'Low' },
]

const totalCount = computed(() => insightsStore.insights.length)
const reviewedCount = computed(() =>
  reviewsStore.reviews.filter(r => r.status !== 'pending').length
)
const progressPct = computed(() =>
  totalCount.value ? Math.round((reviewedCount.value / totalCount.value) * 100) : 0
)
</script>

<style scoped>
.filter-sidebar {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.filter-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.section-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748B;
  margin: 0;
}

/* SelectButton: dark sidebar overrides */
:deep(.filter-select.p-selectbutton) {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  background: transparent;
  border: none;
  padding: 0;
}
:deep(.filter-select .p-togglebutton) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94A3B8;
  padding: 0.3rem 0.625rem;
  font-size: 0.8rem;
  border-radius: 6px;
  transition: all 150ms ease;
}
:deep(.filter-select .p-togglebutton:hover) {
  background: rgba(255, 255, 255, 0.1);
  color: #CBD5E1;
}
:deep(.filter-select .p-togglebutton.p-selected) {
  background: #00C4A0;
  border-color: #00C4A0;
  color: #fff;
}

/* Flagged ToggleButton */
:deep(.filter-toggle.p-togglebutton) {
  width: 100%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94A3B8;
  font-size: 0.825rem;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  justify-content: flex-start;
  transition: all 150ms ease;
}
:deep(.filter-toggle.p-togglebutton.p-selected) {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
  color: #FCA5A5;
}

/* Progress bar (custom — simpler than PrimeVue ProgressBar on dark bg) */
.progress-wrap {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #00C4A0;
  border-radius: 2px;
  transition: width 400ms ease;
}
.progress-text {
  font-size: 0.75rem;
  color: #64748B;
  margin: 0;
}
</style>
```

**Step 2: Verify build passes**

Run: `bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run build 2>&1 | tail -20'`

Expected: zero TypeScript errors.

**Step 3: Commit**

```bash
cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work
git add frontend/src/components/FilterSidebar.vue
git commit -m "feat: rebuild FilterSidebar with SelectButton and dark sidebar styling"
```

---

### Task 3: Rebuild InsightCard.vue with Accordion

**Files:**
- Modify: `frontend/src/components/InsightCard.vue`

Uses PrimeVue 4's `Accordion` / `AccordionPanel` / `AccordionHeader` / `AccordionContent` components. Each card is a single-panel accordion — collapsed by default showing category + headline, expands to reveal summary/evidence/review controls.

PrimeVue 4 Accordion API:
- `<Accordion>` — root, no `v-model` needed for uncontrolled
- `<AccordionPanel value="0">` — single panel; `value` identifies it
- `<AccordionHeader>` — clickable header, renders children + a chevron icon on the right
- `<AccordionContent>` — hidden by default, revealed on click

The outer `.insight-card` div provides card styling; deep CSS overrides strip Accordion's default borders/backgrounds.

**Step 1: Replace the file**

```vue
<template>
  <div class="insight-card">
    <Accordion>
      <AccordionPanel value="0">
        <AccordionHeader>
          <div class="header-inner">
            <div class="header-top">
              <div class="header-meta">
                <span class="category-badge" :style="{ color: CATEGORY_COLORS[insight.category] }">
                  <i :class="['pi', CATEGORY_ICONS[insight.category]]" />
                  {{ CATEGORY_LABELS[insight.category] }}
                </span>
                <Tag :severity="confidenceSeverity" :value="insight.confidence.toUpperCase()" rounded />
                <span class="post-count">
                  <i class="pi pi-comments" />
                  {{ insight.post_count }}
                </span>
              </div>
              <Tag v-if="insight.needs_human_review" severity="warn" value="Needs Review" rounded />
            </div>
            <p class="headline">{{ insight.headline }}</p>
          </div>
        </AccordionHeader>
        <AccordionContent>
          <div class="card-body">
            <p class="summary">{{ insight.summary }}</p>

            <div class="evidence-block">
              <p class="section-label">Evidence</p>
              <blockquote v-for="(q, i) in insight.evidence" :key="i" class="quote">{{ q }}</blockquote>
            </div>

            <div class="action-block">
              <p class="section-label">Product action</p>
              <p class="action-text">{{ insight.product_action }}</p>
            </div>

            <p v-if="insight.canadian_context" class="canadian-context">
              <i class="pi pi-map-marker" />
              {{ insight.canadian_context }}
            </p>

            <div class="review-controls">
              <Select
                v-model="localStatus"
                :options="STATUS_OPTIONS"
                optionLabel="label"
                optionValue="value"
                placeholder="Set status"
                class="status-select"
              />
              <Textarea v-model="localNote" placeholder="Add note or ticket link…" rows="2" autoResize />
              <Button label="Save" :loading="saving" @click="handleSave" size="small" />
            </div>
          </div>
        </AccordionContent>
      </AccordionPanel>
    </Accordion>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Accordion from 'primevue/accordion'
import AccordionPanel from 'primevue/accordionpanel'
import AccordionHeader from 'primevue/accordionheader'
import AccordionContent from 'primevue/accordioncontent'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'
import { useReviewsStore } from '@/stores/reviews'
import type { Insight } from '@/types'

const props = defineProps<{ insight: Insight }>()

const reviewsStore = useReviewsStore()
const toast = useToast()
const saving = ref(false)

const existingReview = computed(() => reviewsStore.getReview(props.insight.id))
const localStatus = ref(existingReview.value?.status ?? 'pending')
const localNote = ref(existingReview.value?.note ?? '')

watch(existingReview, r => {
  if (r) { localStatus.value = r.status; localNote.value = r.note }
})

async function handleSave() {
  saving.value = true
  try {
    await reviewsStore.saveReview(props.insight.id, { status: localStatus.value, note: localNote.value })
    toast.add({ severity: 'success', summary: 'Saved', life: 2000 })
  } catch {
    toast.add({ severity: 'error', summary: 'Save failed', life: 3000 })
  } finally {
    saving.value = false
  }
}

const CATEGORY_COLORS: Record<string, string> = {
  roadmap: '#3B82F6', friction: '#EF4444', win: '#00C4A0', other: '#6B7280',
}
const CATEGORY_ICONS: Record<string, string> = {
  roadmap: 'pi-map', friction: 'pi-bolt', win: 'pi-trophy', other: 'pi-bookmark',
}
const CATEGORY_LABELS: Record<string, string> = {
  roadmap: 'Roadmap', friction: 'Friction', win: 'Win', other: 'Other',
}

const STATUS_OPTIONS = [
  { label: 'Pending',             value: 'pending' },
  { label: 'Escalate to product', value: 'escalate_to_product' },
  { label: 'Under investigation', value: 'under_investigation' },
  { label: 'Known issue',         value: 'known_issue' },
  { label: 'Out of scope',        value: 'out_of_scope' },
  { label: 'Dismissed',           value: 'dismissed' },
]

const confidenceSeverity = computed(() =>
  ({ high: 'success', medium: 'warn', low: 'danger' } as Record<string, string>)[props.insight.confidence] ?? 'info'
)
</script>

<style scoped>
/* Card container — provides border + radius + hover shadow */
.insight-card {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--p-surface-200);
  background: var(--p-surface-0);
  transition: box-shadow 150ms ease;
}
.insight-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.07);
}

/* Strip Accordion's default visual chrome */
:deep(.p-accordion) {
  border: none;
  background: transparent;
}
:deep(.p-accordionpanel) {
  border: none;
  background: transparent;
}
:deep(.p-accordionheader) {
  background: transparent;
  border: none;
  padding: 1rem 1.25rem;
}
:deep(.p-accordionheader:hover) {
  background: var(--p-surface-50);
}
:deep(.p-accordioncontent-content) {
  padding: 0 1.25rem 1.25rem;
  border-top: 1px solid var(--p-surface-100);
}

/* Header layout */
.header-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-meta {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  flex-wrap: wrap;
}
.category-badge {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  font-weight: 600;
}
.post-count {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: var(--p-surface-400);
}
.post-count .pi { font-size: 0.75rem; }
.headline {
  font-size: 1rem;
  font-weight: 700;
  color: var(--p-surface-900);
  margin: 0;
  line-height: 1.4;
  text-align: left;
}

/* Expanded body */
.card-body {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  padding-top: 0.875rem;
}
.summary {
  font-size: 0.9rem;
  color: var(--p-surface-600);
  line-height: 1.6;
  margin: 0;
}
.section-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--p-surface-400);
  margin: 0 0 0.375rem;
}
.quote {
  border-left: 3px solid var(--p-primary-200);
  margin: 0.25rem 0;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  color: var(--p-surface-600);
  font-style: italic;
  background: var(--p-surface-50);
  border-radius: 0 6px 6px 0;
}
.action-text {
  font-size: 0.9rem;
  color: var(--p-surface-700);
  margin: 0;
  line-height: 1.6;
}
.canadian-context {
  display: flex;
  align-items: flex-start;
  gap: 0.375rem;
  font-size: 0.825rem;
  color: var(--p-surface-500);
  background: var(--p-surface-50);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  margin: 0;
}
.review-controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--p-surface-100);
}
.status-select { width: 100%; }
</style>
```

**Step 2: Verify build passes**

Run: `bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run build 2>&1 | tail -20'`

Expected: zero TypeScript errors.

**Step 3: Commit**

```bash
cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work
git add frontend/src/components/InsightCard.vue
git commit -m "feat: rebuild InsightCard as accordion with PrimeIcons"
```

---

### Task 4: Reskin TopicsChart.vue

**Files:**
- Modify: `frontend/src/components/TopicsChart.vue`

Updates hard-coded hex colors to match the new theme palette. Category color for `roadmap` changes from `#2563EB` to `#3B82F6` (lighter blue), `win` from `#059669` to `#00C4A0` (mint). Chart gridlines and tick colors updated to use softer values. Chart card gets a slight shadow on hover.

**Step 1: Replace the file**

```vue
<template>
  <div class="chart-card">
    <h3 class="chart-title">Top topics by post volume</h3>
    <Chart type="bar" :data="chartData" :options="chartOptions" style="height: 280px" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Chart from 'primevue/chart'
import type { Insight } from '@/types'

const CATEGORY_COLORS: Record<string, string> = {
  roadmap:  '#3B82F6',
  friction: '#EF4444',
  win:      '#00C4A0',
  other:    '#94A3B8',
}

const props = defineProps<{ insights: Insight[] }>()

const chartData = computed(() => ({
  labels: props.insights.map(i => i.headline.length > 42 ? i.headline.slice(0, 42) + '…' : i.headline),
  datasets: [{
    data: props.insights.map(i => i.post_count),
    backgroundColor: props.insights.map(i => CATEGORY_COLORS[i.category] ?? '#94A3B8'),
    borderRadius: 6,
  }],
}))

const chartOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { color: '#F1F3F6' }, ticks: { color: '#94A3B8', font: { size: 11 } } },
    y: { grid: { display: false }, ticks: { color: '#374151', font: { size: 12 } } },
  },
}
</script>

<style scoped>
.chart-card {
  background: var(--p-surface-0);
  border: 1px solid var(--p-surface-200);
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  transition: box-shadow 150ms ease;
}
.chart-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.chart-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--p-surface-700);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0 0 1rem;
}
</style>
```

**Step 2: Verify build passes**

Run: `bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run build 2>&1 | tail -20'`

Expected: zero TypeScript errors.

**Step 3: Commit**

```bash
cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work
git add frontend/src/components/TopicsChart.vue
git commit -m "feat: reskin TopicsChart to match new theme palette"
```

---

### Task 5: Update Dashboard.vue layout

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

Changes:
1. Sidebar background to dark navy `#1C2333` with light brand text
2. Brand name styled in mint green
3. Section headers improved (uppercase label style for "Insight Cards" section)
4. `cards-grid` renamed to `cards-list` (same flex-column, just clearer naming)

No script changes — same imports and `onMounted` logic.

**Step 1: Replace the file**

```vue
<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <i class="pi pi-chart-bar brand-icon" />
        <span class="brand-name">WS Intelligence</span>
      </div>
      <FilterSidebar />
    </aside>

    <main class="main-content">
      <header class="page-header">
        <h1 class="page-title">Community Intelligence</h1>
        <p class="page-subtitle">AI finds the signal. You decide what to build.</p>
      </header>

      <KpiTiles v-if="insightsStore.stats" :stats="insightsStore.stats" />
      <TopicsChart :insights="insightsStore.topByVolume" />

      <div class="cards-header">
        <span class="cards-label">Insight Cards</span>
        <span class="cards-count">{{ insightsStore.filtered.length }} insights</span>
      </div>

      <div v-if="insightsStore.loading" class="loading-state">
        <ProgressSpinner />
      </div>
      <div v-else-if="insightsStore.filtered.length === 0" class="empty-state">
        <i class="pi pi-inbox" style="font-size: 2rem; opacity: 0.3" />
        <p>No insights match your filters.</p>
      </div>
      <div v-else class="cards-list">
        <InsightCard
          v-for="insight in insightsStore.filtered"
          :key="insight.id"
          :insight="insight"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import ProgressSpinner from 'primevue/progressspinner'
import KpiTiles from '@/components/KpiTiles.vue'
import TopicsChart from '@/components/TopicsChart.vue'
import FilterSidebar from '@/components/FilterSidebar.vue'
import InsightCard from '@/components/InsightCard.vue'
import { useInsightsStore } from '@/stores/insights'
import { useReviewsStore } from '@/stores/reviews'

const insightsStore = useInsightsStore()
const reviewsStore = useReviewsStore()

onMounted(async () => {
  await Promise.all([insightsStore.fetchAll(), reviewsStore.fetchReviews()])
})
</script>

<style scoped>
/* Layout */
.dashboard { display: flex; min-height: 100vh; background: var(--p-surface-50); }

/* Sidebar */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #1C2333;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 1.25rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-icon {
  font-size: 1.125rem;
  color: #00C4A0;
}
.brand-name {
  font-size: 0.9375rem;
  font-weight: 700;
  color: #F1F5F9;
  letter-spacing: -0.01em;
}

/* Main content */
.main-content {
  flex: 1;
  padding: 2rem 2rem 3rem;
  max-width: 1100px;
}
.page-header { margin-bottom: 1.75rem; }
.page-title {
  font-size: 1.625rem;
  font-weight: 800;
  color: var(--p-surface-900);
  margin: 0;
  letter-spacing: -0.02em;
}
.page-subtitle {
  font-size: 0.875rem;
  color: var(--p-surface-400);
  margin: 0.25rem 0 0;
}

/* Section header */
.cards-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 0.875rem;
}
.cards-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--p-surface-500);
}
.cards-count {
  font-size: 0.875rem;
  color: var(--p-surface-400);
}

/* Card list */
.cards-list { display: flex; flex-direction: column; gap: 0.75rem; }

/* States */
.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  color: var(--p-surface-400);
}
</style>
```

**Step 2: Verify build passes**

Run: `bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run build 2>&1 | tail -20'`

Expected: `✓ built in` with zero TypeScript errors.

**Step 3: Commit**

```bash
cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work
git add frontend/src/views/Dashboard.vue
git commit -m "feat: update Dashboard with dark sidebar and modern section headers"
```

---

### Task 6: Import PrimeIcons CSS

**Files:**
- Modify: `frontend/src/main.ts`

PrimeIcons is installed (`primeicons` in package.json) but the CSS must be imported explicitly. Without this, all `pi-*` icons render as empty boxes.

**Step 1: Read the current main.ts**

Read: `frontend/src/main.ts`

**Step 2: Add PrimeIcons import**

The file currently imports `primevue/resources/...` or similar. Add this import **before** any other imports:

```typescript
import 'primeicons/primeicons.css'
```

The final `main.ts` should look like:

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import { WealthsimpleTheme } from '@/theme/wealthsimple'
import 'primeicons/primeicons.css'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.use(PrimeVue, { theme: { preset: WealthsimpleTheme, options: { darkModeSelector: false } } })
app.use(ToastService)
app.mount('#app')
```

> Note: Read the actual `main.ts` first to see its exact current content before editing. Only add the `primeicons/primeicons.css` import line — do not change anything else.

**Step 3: Verify build passes**

Run: `bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run build 2>&1 | tail -20'`

Expected: `✓ built in` with zero TypeScript errors.

**Step 4: Commit**

```bash
cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work
git add frontend/src/main.ts
git commit -m "feat: import PrimeIcons CSS so icons render correctly"
```

---

## Visual Verification

After all tasks complete, start the dev server and verify visually:

```bash
# Terminal 1 — API
cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work
uv run uvicorn api.main:app --reload

# Terminal 2 — Frontend
bash -c 'export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && cd /home/joni/.config/superpowers/worktrees/wealthsimple-community-intel/ui-work/frontend && npm run dev'
```

Open http://localhost:5173 and confirm:
- [ ] Sidebar is dark navy, brand in mint green, filter labels are light gray
- [ ] Category SelectButton buttons glow mint green when selected
- [ ] KPI tiles have colored left border + icon circles
- [ ] Insight cards are collapsed by default, expand on click with smooth animation
- [ ] Chart bars use new color palette
- [ ] PrimeIcons render (not empty boxes)
