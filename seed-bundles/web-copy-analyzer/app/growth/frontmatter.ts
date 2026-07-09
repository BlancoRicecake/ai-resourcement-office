/**
 * Minimal frontmatter serialize/parse for personas/<slug>.md (design.md
 * §6-1). Deliberately hand-rolled (no yaml dependency, 원칙① minimal runtime
 * deps) — supports exactly the shapes personas need: scalar strings and
 * string arrays. Any deviation (missing `---` fences, malformed array/scalar
 * lines) throws FrontmatterParseError so callers can apply 문제표 #9's
 * "isolate this file, keep loading the rest" behavior.
 */

export class FrontmatterParseError extends Error {}

const FENCE = "---";

export function serializeFrontmatter(data: Record<string, string | number | string[]>, body: string): string {
  const lines: string[] = [FENCE];
  for (const [key, value] of Object.entries(data)) {
    if (Array.isArray(value)) {
      if (value.length === 0) {
        lines.push(`${key}: []`);
        continue;
      }
      lines.push(`${key}:`);
      for (const item of value) {
        lines.push(`  - ${escapeScalar(item)}`);
      }
    } else {
      lines.push(`${key}: ${escapeScalar(String(value))}`);
    }
  }
  lines.push(FENCE);
  return `${lines.join("\n")}\n${body}\n`;
}

function escapeScalar(value: string): string {
  // Values are single-line by construction (persona fields are short strings);
  // collapse any embedded newlines defensively rather than breaking the format.
  return value.replace(/\r?\n/g, " ").trim();
}

export interface ParsedFrontmatter {
  data: Record<string, string | string[]>;
  body: string;
}

export function parseFrontmatter(raw: string): ParsedFrontmatter {
  const lines = raw.split(/\r?\n/);
  if (lines[0] !== FENCE) {
    throw new FrontmatterParseError("missing opening frontmatter fence");
  }
  let i = 1;
  const data: Record<string, string | string[]> = {};
  while (i < lines.length && lines[i] !== FENCE) {
    const line = lines[i];
    if (line === undefined) throw new FrontmatterParseError("unexpected end of frontmatter");
    if (line.trim().length === 0) {
      i++;
      continue;
    }
    const scalarMatch = /^([a-zA-Z_][a-zA-Z0-9_]*):\s*(\[\])?\s*(.*)$/.exec(line);
    if (!scalarMatch) {
      throw new FrontmatterParseError(`malformed frontmatter line: ${JSON.stringify(line)}`);
    }
    const key = scalarMatch[1] as string;
    const emptyArrayMarker = scalarMatch[2];
    const rest = (scalarMatch[3] ?? "").trim();
    if (emptyArrayMarker === "[]") {
      data[key] = [];
      i++;
      continue;
    }
    if (rest.length > 0) {
      data[key] = rest;
      i++;
      continue;
    }
    // Array form: subsequent "  - item" lines.
    const items: string[] = [];
    i++;
    while (i < lines.length) {
      const itemLine = lines[i];
      if (itemLine === undefined) break;
      const itemMatch = /^\s{2}-\s?(.*)$/.exec(itemLine);
      if (!itemMatch) break;
      items.push((itemMatch[1] ?? "").trim());
      i++;
    }
    data[key] = items;
  }
  if (lines[i] !== FENCE) {
    throw new FrontmatterParseError("missing closing frontmatter fence");
  }
  const body = lines
    .slice(i + 1)
    .join("\n")
    .replace(/\n+$/, "");
  return { data, body };
}
