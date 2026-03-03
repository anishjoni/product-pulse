import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const CATEGORY_COLORS: Record<string, string> = {
  feature_request: "#3B82F6",
  bug_report: "#EF4444",
  complaint: "#F97316",
  praise: "#22C55E",
  general_discussion: "#6B7280",
};

export const CATEGORY_LABELS: Record<string, string> = {
  feature_request: "Feature Request",
  bug_report: "Bug Report",
  complaint: "Complaint",
  praise: "Praise",
  general_discussion: "Discussion",
};

export const ALL_CATEGORIES = [
  "feature_request",
  "bug_report",
  "complaint",
  "praise",
  "general_discussion",
] as const;

export function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return "Never";
  const date = new Date(isoString.endsWith("Z") ? isoString : isoString + "Z");
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  return `${Math.floor(diffH / 24)}d ago`;
}

export function formatPct(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${Math.round(value)}%`;
}
