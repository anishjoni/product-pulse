<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="sidebar-brand">
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
        <h2 class="cards-title">Insight Cards</h2>
        <span class="cards-count">{{ insightsStore.filtered.length }} insights</span>
      </div>

      <div v-if="insightsStore.loading" class="loading-state">
        <ProgressSpinner />
      </div>
      <div v-else-if="insightsStore.filtered.length === 0" class="empty-state">
        <p>No insights match your filters.</p>
      </div>
      <div v-else class="cards-grid">
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
.dashboard { display: flex; min-height: 100vh; background: var(--p-surface-50); }
.sidebar { width: 240px; flex-shrink: 0; background: var(--p-surface-0); border-right: 1px solid var(--p-surface-200); display: flex; flex-direction: column; }
.sidebar-brand { padding: 1.25rem 1rem; border-bottom: 1px solid var(--p-surface-200); }
.brand-name { font-size: 1rem; font-weight: 700; color: var(--p-primary-500); }
.main-content { flex: 1; padding: 2rem; max-width: 1100px; }
.page-header { margin-bottom: 1.5rem; }
.page-title { font-size: 1.75rem; font-weight: 800; color: var(--p-surface-900); margin: 0; }
.page-subtitle { font-size: 0.9rem; color: var(--p-surface-500); margin: 0.25rem 0 0; }
.cards-header { display: flex; align-items: baseline; gap: 0.75rem; margin-bottom: 1rem; }
.cards-title { font-size: 1.125rem; font-weight: 700; margin: 0; }
.cards-count { font-size: 0.875rem; color: var(--p-surface-500); }
.cards-grid { display: flex; flex-direction: column; gap: 1rem; }
.loading-state, .empty-state { text-align: center; padding: 3rem; color: var(--p-surface-500); }
</style>
