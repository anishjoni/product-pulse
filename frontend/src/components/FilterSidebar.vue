<template>
  <div class="filter-sidebar">
    <h3 class="filter-title">Filters</h3>

    <div class="filter-group">
      <p class="filter-group-label">Category</p>
      <div v-for="cat in CATEGORIES" :key="cat.value" class="filter-item">
        <Checkbox v-model="filters.categories" :inputId="cat.value" :value="cat.value" />
        <label :for="cat.value">{{ cat.label }}</label>
      </div>
    </div>

    <div class="filter-group">
      <p class="filter-group-label">Confidence</p>
      <div v-for="conf in CONFIDENCES" :key="conf.value" class="filter-item">
        <Checkbox v-model="filters.confidences" :inputId="conf.value" :value="conf.value" />
        <label :for="conf.value">{{ conf.label }}</label>
      </div>
    </div>

    <div class="filter-group">
      <div class="filter-item">
        <Checkbox v-model="filters.flaggedOnly" inputId="flagged" binary />
        <label for="flagged">Flagged for review only</label>
      </div>
    </div>

    <div class="review-progress">
      <p class="filter-group-label">Review progress</p>
      <ProgressBar :value="progressPct" />
      <p class="progress-text">{{ reviewedCount }}/{{ totalCount }} ({{ progressPct }}%)</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Checkbox from 'primevue/checkbox'
import ProgressBar from 'primevue/progressbar'
import { useInsightsStore } from '@/stores/insights'
import { useReviewsStore } from '@/stores/reviews'

const insightsStore = useInsightsStore()
const reviewsStore = useReviewsStore()
const filters = insightsStore.filters

const CATEGORIES = [
  { value: 'roadmap',  label: '🗺️ Roadmap' },
  { value: 'friction', label: '🔥 Friction' },
  { value: 'win',      label: '🏆 Win' },
  { value: 'other',    label: '📌 Other' },
]
const CONFIDENCES = [
  { value: 'high',   label: '🟢 High' },
  { value: 'medium', label: '🟡 Medium' },
  { value: 'low',    label: '🔴 Low' },
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
.filter-sidebar { padding: 1rem; display: flex; flex-direction: column; gap: 1.25rem; }
.filter-title { font-size: 1rem; font-weight: 700; color: var(--p-surface-900); margin: 0; }
.filter-group { display: flex; flex-direction: column; gap: 0.5rem; }
.filter-group-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--p-surface-500); margin: 0; }
.filter-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; }
.progress-text { font-size: 0.8125rem; color: var(--p-surface-500); margin: 0.25rem 0 0; }
</style>
