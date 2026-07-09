/**
 * snake_case (wire, design.md §2-3) <-> camelCase (core, core/types.ts)
 * boundary translation. Generic + recursive: every object key is re-cased,
 * every array is mapped element-wise, primitives pass through untouched
 * (enum/const *values* like "above_fold" are never keys, so they are never
 * touched by this — they stay exactly as the schema declares).
 */

function snakeToCamel(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_, c: string) => c.toUpperCase());
}

function camelToSnake(key: string): string {
  return key
    .replace(/([a-z])([0-9])/g, "$1_$2") // letter->digit boundary (e.g. "per100Words" -> "per_100Words")
    .replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`);
}

function deepMapKeys(value: unknown, mapKey: (key: string) => string): unknown {
  if (Array.isArray(value)) {
    return value.map((v) => deepMapKeys(v, mapKey));
  }
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[mapKey(k)] = deepMapKeys(v, mapKey);
    }
    return out;
  }
  return value;
}

/** wire (snake_case) -> core (camelCase), recursively. */
export function toCamelDeep<T = unknown>(value: unknown): T {
  return deepMapKeys(value, snakeToCamel) as T;
}

/** core (camelCase) -> wire (snake_case), recursively. */
export function toSnakeDeep<T = unknown>(value: unknown): T {
  return deepMapKeys(value, camelToSnake) as T;
}
