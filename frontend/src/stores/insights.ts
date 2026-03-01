import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import type { Insight, Stats, Category, Confidence } from '@/types'

export const useInsightsStore = defineStore('insights', () => {
  const insights = ref<Insight[]>([])
  const stats = ref<Stats | null>(null)
  const loading = ref(false)

  const filters = ref({
    categories: ['roadmap', 'friction', 'win', 'other'] as Category[],
    confidences: ['high', 'medium', 'low'] as Confidence[],
    flaggedOnly: false,
  })

  const filtered = computed(() =>
    insights.value.filter(i => {
      if (!filters.value.categories.includes(i.category)) return false
      if (!filters.value.confidences.includes(i.confidence)) return false
      if (filters.value.flaggedOnly && !i.needs_human_review) return false
      return true
    })
  )

  const topByVolume = computed(() =>
    [...insights.value].sort((a, b) => b.post_count - a.post_count).slice(0, 8)
  )

  async function fetchAll() {
    loading.value = true
    try {
      const [insightData, statsData] = await Promise.all([api.getInsights(), api.getStats()])
      insights.value = insightData
      stats.value = statsData
    } finally {
      loading.value = false
    }
  }

  return { insights, stats, loading, filters, filtered, topByVolume, fetchAll }
})
