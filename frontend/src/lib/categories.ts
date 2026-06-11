import type { Category } from "@/lib/api";
import type { MessageKey } from "@/lib/i18n/messages";

export type CategoryLike = {
  name?: string;
  slug?: string | null;
  category_name?: string;
  category_slug?: string | null;
};

export function getCategoryLabel(
  category: CategoryLike,
  t: (key: MessageKey, params?: Record<string, string | number>) => string
): string {
  const slug = category.slug ?? category.category_slug ?? null;
  const fallback = category.name ?? category.category_name ?? "";

  if (slug) {
    const key = `categories.${slug}` as MessageKey;
    const translated = t(key);
    if (translated !== key) return translated;
  }

  return fallback;
}

export function isCustomCategory(category: Category): boolean {
  return category.user_id != null;
}

export const CATEGORY_COLOR_OPTIONS = [
  "#16a34a",
  "#059669",
  "#2563eb",
  "#9333ea",
  "#db2777",
  "#dc2626",
  "#ea580c",
  "#d97706",
  "#64748b",
];
