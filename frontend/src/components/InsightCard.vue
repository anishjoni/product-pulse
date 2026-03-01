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
