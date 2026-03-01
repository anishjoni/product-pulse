<template>
  <div class="kpi-row">
    <div v-for="tile in tiles" :key="tile.label" class="kpi-card">
      <span class="kpi-value">{{ tile.value }}</span>
      <span class="kpi-label">{{ tile.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Stats } from '@/types'

const props = defineProps<{ stats: Stats }>()

const tiles = computed(() => [
  { label: 'Posts analyzed',  value: props.stats.total_posts.toLocaleString() },
  { label: 'Insight cards',   value: props.stats.total_insights },
  { label: 'Pending review',  value: props.stats.pending_review },
  { label: 'Flagged',         value: props.stats.flagged_for_review },
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
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--p-surface-900);
  line-height: 1;
}
.kpi-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--p-surface-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
