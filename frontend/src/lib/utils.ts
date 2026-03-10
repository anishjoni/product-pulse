import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const CATEGORY_COLORS: Record<string, string> = {
  feature_request: "#335C67",
  bug_report: "#540B0E",
  complaint: "#9E2A2B",
  praise: "#E09F3E",
  general_discussion: "#FFF3B0",
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

export function formatSourceRef(sourceType: string, sourceRef: string): string {
  switch (sourceType) {
    case "reddit":
      return `r/${sourceRef}`;
    case "google_play": {
      const [pkg, country] = sourceRef.split(":");
      // Drop leading TLD segment (com / org / net / io / co)
      const parts = pkg.split(".").filter((p) => !["com", "org", "net", "io", "co"].includes(p));
      const name = parts.join(" · ") || pkg;
      return country ? `${name} · ${country.toUpperCase()}` : name;
    }
    case "apple_app_store": {
      const [, country] = sourceRef.split(":");
      return country ? `App Store · ${country.toUpperCase()}` : "App Store";
    }
    default:
      return sourceRef;
  }
}

export function formatPct(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${Math.round(value)}%`;
}
