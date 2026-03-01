import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import type { Review, ReviewUpdate } from '@/types'

export const useReviewsStore = defineStore('reviews', () => {
  const reviews = ref<Review[]>([])
  const saving = ref(false)

  function getReview(insightId: string): Review | undefined {
    return reviews.value.find(r => r.insight_id === insightId)
  }

  async function fetchReviews() {
    reviews.value = await api.getReviews()
  }

  async function saveReview(insightId: string, update: ReviewUpdate) {
    saving.value = true
    try {
      const saved = await api.updateReview(insightId, update)
      const idx = reviews.value.findIndex(r => r.insight_id === insightId)
      if (idx >= 0) reviews.value[idx] = saved
      else reviews.value.push(saved)
    } finally {
      saving.value = false
    }
  }

  return { reviews, saving, getReview, fetchReviews, saveReview }
})
