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
