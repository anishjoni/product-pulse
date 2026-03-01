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
