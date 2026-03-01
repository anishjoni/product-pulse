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
