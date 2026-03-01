import axios from 'axios'
import type { Insight, Review, ReviewUpdate, Stats } from '@/types'

const http = axios.create({ baseURL: '/api' })

export const api = {
  getStats: (): Promise<Stats> =>
    http.get('/stats').then(r => r.data),

  getInsights: (params?: { category?: string; confidence?: string; flagged?: boolean }): Promise<Insight[]> =>
    http.get('/insights', { params }).then(r => r.data),

  getInsight: (id: string): Promise<Insight> =>
    http.get(`/insights/${id}`).then(r => r.data),

  getReviews: (): Promise<Review[]> =>
    http.get('/reviews').then(r => r.data),

  updateReview: (insightId: string, update: ReviewUpdate): Promise<Review> =>
    http.patch(`/reviews/${insightId}`, update).then(r => r.data),
}
