/**
 * Minimal JSON Schema (sub)set validator for MCP tool inputSchemas
 * (design.md §5: "모든 툴 inputSchema도 사람 입력과 동일 수준 검증"). This is
 * intentionally NOT a general-purpose JSON Schema engine — it covers exactly
 * the shapes the 12 tool schemas in core/tool-schemas.ts use: object/array/
 * string/integer/number/boolean, required, properties, additionalProperties
 * false, enum/const, min/maxLength, minimum/maximum, maxItems, pattern,
 * format:"uri". Anything the schema declares as a bare `{"type":"object"}`
 * with no `properties` (e.g. `parsed_page`, `before`) is accepted as-is —
 * that structural validation is the core functions' job (they throw on
 * malformed shape), this layer's job is enforcing the wire-contract caps
 * (§5 크기 상한) that core does not itself check (e.g. remember's
 * content/context maxLength).
 */

export class ToolInputValidationError extends Error {
  constructor(
    public readonly errors: string[]
  ) {
    super(`tool input validation failed: ${errors.join("; ")}`);
    this.name = "ToolInputValidationError";
  }
}

type JsonSchema = Record<string, unknown>;

function typeOf(value: unknown): string {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value;
}

function validateNode(schema: JsonSchema, value: unknown, path: string, errors: string[]): void {
  if (schema["const"] !== undefined && value !== schema["const"]) {
    errors.push(`${path}: expected const ${JSON.stringify(schema["const"])}`);
    return;
  }
  if (Array.isArray(schema["enum"]) && !schema["enum"].includes(value)) {
    errors.push(`${path}: expected one of ${JSON.stringify(schema["enum"])}, got ${JSON.stringify(value)}`);
    return;
  }

  const type = schema["type"] as string | undefined;
  if (type === undefined) return; // untyped/bare schema (e.g. parsed_page) — accept as-is.

  const actual = typeOf(value);
  const normalizedActual = type === "integer" && actual === "number" ? "integer" : actual;
  if (type === "integer") {
    if (actual !== "number" || !Number.isInteger(value)) {
      errors.push(`${path}: expected integer, got ${actual}`);
      return;
    }
  } else if (normalizedActual !== type) {
    errors.push(`${path}: expected ${type}, got ${actual}`);
    return;
  }

  if (type === "string") {
    const s = value as string;
    if (typeof schema["maxLength"] === "number" && s.length > (schema["maxLength"] as number)) {
      errors.push(`${path}: exceeds maxLength ${schema["maxLength"]}`);
    }
    if (typeof schema["minLength"] === "number" && s.length < (schema["minLength"] as number)) {
      errors.push(`${path}: shorter than minLength ${schema["minLength"]}`);
    }
    if (typeof schema["pattern"] === "string" && !new RegExp(schema["pattern"] as string).test(s)) {
      errors.push(`${path}: does not match pattern ${schema["pattern"]}`);
    }
    if (schema["format"] === "uri") {
      try {
        new URL(s);
      } catch {
        errors.push(`${path}: not a valid URI`);
      }
    }
  }

  if (type === "integer" || type === "number") {
    const n = value as number;
    if (typeof schema["minimum"] === "number" && n < (schema["minimum"] as number)) {
      errors.push(`${path}: below minimum ${schema["minimum"]}`);
    }
    if (typeof schema["maximum"] === "number" && n > (schema["maximum"] as number)) {
      errors.push(`${path}: above maximum ${schema["maximum"]}`);
    }
  }

  if (type === "array") {
    const arr = value as unknown[];
    if (typeof schema["maxItems"] === "number" && arr.length > (schema["maxItems"] as number)) {
      errors.push(`${path}: exceeds maxItems ${schema["maxItems"]}`);
    }
    const items = schema["items"] as JsonSchema | undefined;
    if (items) {
      arr.forEach((item, i) => validateNode(items, item, `${path}[${i}]`, errors));
    }
  }

  if (type === "object") {
    const obj = value as Record<string, unknown>;
    const properties = (schema["properties"] as Record<string, JsonSchema> | undefined) ?? {};
    const required = (schema["required"] as string[] | undefined) ?? [];
    for (const key of required) {
      if (!(key in obj)) errors.push(`${path}.${key}: required property missing`);
    }
    if (schema["additionalProperties"] === false) {
      for (const key of Object.keys(obj)) {
        if (!(key in properties)) errors.push(`${path}.${key}: additional property not allowed`);
      }
    }
    for (const [key, subSchema] of Object.entries(properties)) {
      if (key in obj) validateNode(subSchema, obj[key], `${path}.${key}`, errors);
    }
  }
}

/** Fills in top-level `default` values for missing object properties (recursively one level, matching this project's schemas). */
export function applyDefaults(schema: JsonSchema, value: unknown): unknown {
  if (schema["type"] !== "object" || typeof value !== "object" || value === null || Array.isArray(value)) return value;
  const properties = (schema["properties"] as Record<string, JsonSchema> | undefined) ?? {};
  const result: Record<string, unknown> = { ...(value as Record<string, unknown>) };
  for (const [key, subSchema] of Object.entries(properties)) {
    if (!(key in result) && subSchema["default"] !== undefined) {
      result[key] = subSchema["default"];
    }
  }
  return result;
}

export function validateToolInput(schema: JsonSchema, value: unknown): void {
  const errors: string[] = [];
  validateNode(schema, value, "input", errors);
  if (errors.length > 0) throw new ToolInputValidationError(errors);
}
