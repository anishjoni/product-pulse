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
