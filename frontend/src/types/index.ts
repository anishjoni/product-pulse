export type Category = 'roadmap' | 'friction' | 'win' | 'other'
export type Confidence = 'high' | 'medium' | 'low'
export type ReviewStatus =
  | 'pending'
  | 'escalate_to_product'
  | 'under_investigation'
  | 'known_issue'
  | 'out_of_scope'
  | 'dismissed'

export interface Insight {
  id: string
  headline: string
  category: Category
  confidence: Confidence
  summary: string
  evidence: string[]
  product_action: string
  volume_signal: string
  needs_human_review: boolean
  review_reason: string | null
  canadian_context: string | null
  post_count: number
}

export interface Review {
  insight_id: string
  status: ReviewStatus
  note: string
  updated_at: string
}

export interface ReviewUpdate {
  status: ReviewStatus
  note: string
}

export interface Stats {
  total_posts: number
  total_insights: number
  pending_review: number
  flagged_for_review: number
}
