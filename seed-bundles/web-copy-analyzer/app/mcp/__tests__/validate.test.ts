import { test } from "node:test";
import assert from "node:assert/strict";
import { applyDefaults, validateToolInput, ToolInputValidationError } from "../validate.js";
import { FETCH_PAGE_TOOL, REMEMBER_TOOL, SAVE_PERSONA_TOOL } from "../../core/tool-schemas.js";

test("validateToolInput: rejects additionalProperties per §5", () => {
  assert.throws(
    () => validateToolInput(REMEMBER_TOOL.inputSchema, { kind: "decision", content: "x", extra_field: 1 }),
    ToolInputValidationError
  );
});

test("validateToolInput: rejects content exceeding maxLength (core does not itself check this)", () => {
  assert.throws(
    () => validateToolInput(REMEMBER_TOOL.inputSchema, { kind: "decision", content: "x".repeat(2001) }),
    ToolInputValidationError
  );
});

test("validateToolInput: rejects missing required fields", () => {
  assert.throws(() => validateToolInput(SAVE_PERSONA_TOOL.inputSchema, { name: "x" }), ToolInputValidationError);
});

test("validateToolInput: accepts a well-formed save_persona input", () => {
  assert.doesNotThrow(() =>
    validateToolInput(SAVE_PERSONA_TOOL.inputSchema, {
      name: "Sam",
      attributes: { role: "founder", pains: ["no time"], vocabulary: ["MRR"] },
    })
  );
});

test("validateToolInput: rejects a url failing the ^https?:// pattern", () => {
  assert.throws(() => validateToolInput(FETCH_PAGE_TOOL.inputSchema, { url: "ftp://example.com" }), ToolInputValidationError);
});

test("applyDefaults: fills timeout_ms/max_bytes/allow_local defaults for fetch_page", () => {
  const result = applyDefaults(FETCH_PAGE_TOOL.inputSchema, { url: "https://example.com" }) as Record<string, unknown>;
  assert.equal(result["timeout_ms"], 10000);
  assert.equal(result["max_bytes"], 5000000);
  assert.equal(result["allow_local"], false);
});

test("applyDefaults + validateToolInput compose: defaulted input passes validation", () => {
  const withDefaults = applyDefaults(FETCH_PAGE_TOOL.inputSchema, { url: "https://example.com" });
  assert.doesNotThrow(() => validateToolInput(FETCH_PAGE_TOOL.inputSchema, withDefaults));
});
