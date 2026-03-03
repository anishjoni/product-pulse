const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ProductSource {
  id: number;
  source_type: string;
  source_ref: string;
  is_enabled: boolean;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  keywords: string[];
  sources: ProductSource[];
}

export interface CategoryCounts {
  feature_request?: number;
  bug_report?: number;
  complaint?: number;
  praise?: number;
  general_discussion?: number;
  [key: string]: number | undefined;
}

export interface ProductSummary {
  product_id: number;
  product_name: string;
  period: string;
  total_items: number;
  category_counts: CategoryCounts;
  avg_sentiment: number;
  sentiment_trend: "improving" | "declining" | "stable";
  top_trend: string | null;
  last_scout_at: string | null;
  last_scout_status: string | null;
}

export interface FeedbackItem {
  id: number;
  raw_feedback_id: number;
  category: string;
  sentiment: number;
  summary: string;
  topics: string[];
  confidence: number;
  llm_provider: string;
  classified_at: string;
  source: string;
  source_ref: string;
  external_id: string;
  author: string | null;
  url: string | null;
  score: number | null;
  fetched_at: string;
}

export interface FeedbackDetailItem extends FeedbackItem {
  content: string;
  product_id: number;
}

export interface FeedbackPage {
  items: FeedbackItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TrendItem {
  topic: string;
  current_count: number;
  previous_count: number;
  pct_change: number;
  category_breakdown: Record<string, number>;
}

export interface TrendsResponse {
  product_id: number;
  trends: TrendItem[];
  computed_at: string | null;
  period_days: number;
}

export interface ScoutRun {
  id: number;
  product_id: number;
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  items_fetched: number;
  items_classified: number;
  error_message: string | null;
}

export interface FeedbackQueryParams {
  page?: number;
  page_size?: number;
  category?: string;
  source?: string;
  sentiment?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

function toQueryString(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== "" && v !== null
  );
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(v!.toString())}`).join("&");
}

// ---------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------

export function getProducts(): Promise<Product[]> {
  return apiFetch<Product[]>("/products");
}

export function getProduct(id: number): Promise<Product> {
  return apiFetch<Product>(`/products/${id}`);
}

export function getProductBySlug(products: Product[], slug: string): Product | undefined {
  return products.find((p) => p.slug === slug);
}

export function getProductSummary(productId: number, periodDays = 7): Promise<ProductSummary> {
  return apiFetch<ProductSummary>(
    `/products/${productId}/summary?period_days=${periodDays}`
  );
}

export function updateProduct(
  productId: number,
  payload: { keywords: string[]; sources: { source_type: string; source_ref: string }[] }
): Promise<Product> {
  return apiFetch<Product>(`/products/${productId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Scout
// ---------------------------------------------------------------------------

export function triggerScout(productId: number): Promise<ScoutRun> {
  return apiFetch<ScoutRun>(`/products/${productId}/scout`, { method: "POST" });
}

export function getScoutRuns(productId: number): Promise<ScoutRun[]> {
  return apiFetch<ScoutRun[]>(`/products/${productId}/scout-runs`);
}

export function getScoutRun(runId: number): Promise<ScoutRun> {
  return apiFetch<ScoutRun>(`/scout-runs/${runId}`);
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

export function getProductFeedback(
  productId: number,
  params: FeedbackQueryParams = {}
): Promise<FeedbackPage> {
  const qs = toQueryString(params as Record<string, string | number | undefined>);
  return apiFetch<FeedbackPage>(`/products/${productId}/feedback${qs}`);
}

export function getFeedbackItem(feedbackId: number): Promise<FeedbackDetailItem> {
  return apiFetch<FeedbackDetailItem>(`/feedback/${feedbackId}`);
}

// ---------------------------------------------------------------------------
// Trends
// ---------------------------------------------------------------------------

export function getProductTrends(
  productId: number,
  periodDays = 7,
  limit = 10
): Promise<TrendsResponse> {
  return apiFetch<TrendsResponse>(
    `/products/${productId}/trends?period_days=${periodDays}&limit=${limit}`
  );
}
