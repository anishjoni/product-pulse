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
  roadmap:  '#2563EB',
  friction: '#EF4444',
  win:      '#059669',
  other:    '#6B7280',
}

const props = defineProps<{ insights: Insight[] }>()

const chartData = computed(() => ({
  labels: props.insights.map(i => i.headline.length > 42 ? i.headline.slice(0, 42) + '…' : i.headline),
  datasets: [{
    data: props.insights.map(i => i.post_count),
    backgroundColor: props.insights.map(i => CATEGORY_COLORS[i.category] ?? '#6B7280'),
    borderRadius: 6,
  }],
}))

const chartOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { color: '#E5E7EB' }, ticks: { color: '#6B7280' } },
    y: { grid: { display: false }, ticks: { color: '#1A1A1A', font: { size: 12 } } },
  },
}
</script>

<style scoped>
.chart-card {
  background: var(--p-surface-0);
  border: 1px solid var(--p-surface-200);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}
.chart-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--p-surface-900);
  margin: 0 0 1rem;
}
</style>
