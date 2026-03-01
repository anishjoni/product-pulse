<template>
  <div class="insight-card" :class="insight.category">
    <div class="card-header">
      <div class="card-meta">
        <span class="category-badge" :style="{ color: CATEGORY_COLORS[insight.category] }">
          {{ CATEGORY_ICONS[insight.category] }} {{ CATEGORY_LABELS[insight.category] }}
        </span>
        <Tag :severity="confidenceSeverity" :value="insight.confidence.toUpperCase()" rounded />
        <span class="post-count">{{ insight.post_count }} posts</span>
      </div>
      <Tag v-if="insight.needs_human_review" severity="warn" value="⚠ Needs Review" rounded />
    </div>

    <h3 class="headline">{{ insight.headline }}</h3>
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
      🍁 {{ insight.canadian_context }}
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
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
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
  roadmap: '#2563EB', friction: '#EF4444', win: '#059669', other: '#6B7280',
}
const CATEGORY_ICONS: Record<string, string> = {
  roadmap: '🗺️', friction: '🔥', win: '🏆', other: '📌',
}
const CATEGORY_LABELS: Record<string, string> = {
  roadmap: 'Roadmap Opportunity', friction: 'Friction / Pain Point', win: 'Win', other: 'Other',
}

const STATUS_OPTIONS = [
  { label: 'Pending',              value: 'pending' },
  { label: 'Escalate to product',  value: 'escalate_to_product' },
  { label: 'Under investigation',  value: 'under_investigation' },
  { label: 'Known issue',          value: 'known_issue' },
  { label: 'Out of scope',         value: 'out_of_scope' },
  { label: 'Dismissed',            value: 'dismissed' },
]

const confidenceSeverity = computed(() => ({
  high: 'success', medium: 'warn', low: 'danger',
}[props.insight.confidence] ?? 'info'))
</script>

<style scoped>
.insight-card { background: var(--p-surface-0); border: 1px solid var(--p-surface-200); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; gap: 0.875rem; }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; }
.card-meta { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.category-badge { font-size: 0.8125rem; font-weight: 600; }
.post-count { font-size: 0.8125rem; color: var(--p-surface-500); }
.headline { font-size: 1.0625rem; font-weight: 700; color: var(--p-surface-900); margin: 0; }
.summary { font-size: 0.9rem; color: var(--p-surface-700); margin: 0; line-height: 1.6; }
.section-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--p-surface-500); margin: 0 0 0.25rem; }
.quote { border-left: 3px solid var(--p-surface-200); margin: 0.25rem 0; padding-left: 0.75rem; font-size: 0.875rem; color: var(--p-surface-600); font-style: italic; }
.action-text { font-size: 0.9rem; color: var(--p-surface-700); margin: 0; line-height: 1.6; }
.canadian-context { font-size: 0.8125rem; color: var(--p-surface-500); background: var(--p-surface-50); border-radius: 8px; padding: 0.5rem 0.75rem; margin: 0; }
.review-controls { display: flex; flex-direction: column; gap: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--p-surface-100); }
.status-select { width: 100%; }
</style>
