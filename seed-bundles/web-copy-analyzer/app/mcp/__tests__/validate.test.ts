import { test } from "node:test";
import assert from "node:assert/strict";
import { applyDefaults, validateToolInput, ToolInputValidationError } from "../validate.js";
import { COMPARE_REPORT_TOOL, DIAGNOSE_SECTION_TOOL, FETCH_PAGE_TOOL } from "../../core/tool-schemas.js";

const VALID_PERSONA = {
  name: "Sam",
  attributes: { role: "founder", pains: ["no time"], vocabulary: ["MRR"] },
};

test("validateToolInput: rejects additionalProperties per §5", () => {
  assert.throws(
    () => validateToolInput(DIAGNOSE_SECTION_TOOL.inputSchema, { parsed_page: {}, persona: VALID_PERSONA, extra_field: 1 }),
    ToolInputValidationError
  );
});

test("validateToolInput: rejects a rewritten_text exceeding maxLength (core does not itself check this)", () => {
  assert.throws(
    () =>
      validateToolInput(COMPARE_REPORT_TOOL.inputSchema, {
        before: {},
        after: [{ section_id: "s1", rewritten_text: "x".repeat(20001) }],
      }),
    ToolInputValidationError
  );
});

test("validateToolInput: rejects missing required fields", () => {
  assert.throws(() => validateToolInput(DIAGNOSE_SECTION_TOOL.inputSchema, { parsed_page: {} }), ToolInputValidationError);
});

test("validateToolInput: accepts a well-formed diagnose_section input with an inline persona", () => {
  assert.doesNotThrow(() =>
    validateToolInput(DIAGNOSE_SECTION_TOOL.inputSchema, { parsed_page: {}, persona: VALID_PERSONA })
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
