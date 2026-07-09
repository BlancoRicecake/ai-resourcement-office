/**
 * fetchPage — Node-only local page fetch with SSRF guard (design.md §5).
 *
 * ISOLATION: this module imports node:http/https/dns/net and MUST NOT be
 * imported from core/index.ts (the browser-safe barrel). Import it directly
 * via the package's "./fetch-node" export subpath (see package.json).
 *
 * SSRF guard (§5): block RFC1918 / link-local (169.254.0.0/16) / loopback by
 * default; `allowLocal` opts in. DNS is re-resolved and re-validated on
 * every single connection attempt (initial request AND each redirect hop)
 * via a custom `lookup` passed to http(s).request — this defeats DNS
 * rebinding, where a hostname could resolve to a public IP at request time
 * but a private IP at connect time, or where a redirect chain points at a
 * different, private host.
 */

import * as http from "node:http";
import * as https from "node:https";
import * as dns from "node:dns";
import * as net from "node:net";
import { CHALLENGE_SIGNATURES, DEFAULT_MAX_BYTES, DEFAULT_TIMEOUT_MS, MAX_REDIRECTS, MAX_TIMEOUT_MS, MIN_TIMEOUT_MS, MOJIBAKE_RATIO_THRESHOLD } from "./constants.js";
import type { FetchPageOptions, FetchResult } from "./types.js";

export class FetchPageValidationError extends Error {}

function isPrivateOrLocalIPv4(ip: string): boolean {
  const parts = ip.split(".").map(Number);
  if (parts.length !== 4 || parts.some((p) => Number.isNaN(p))) return false;
  const [a, b] = parts as [number, number, number, number];
  if (a === 127) return true; // loopback
  if (a === 10) return true; // RFC1918
  if (a === 172 && b >= 16 && b <= 31) return true; // RFC1918
  if (a === 192 && b === 168) return true; // RFC1918
  if (a === 169 && b === 254) return true; // link-local / cloud metadata (169.254.169.254)
  if (a === 100 && b >= 64 && b <= 127) return true; // CGNAT 100.64.0.0/10
  if (a === 192 && b === 0) return true; // 192.0.0.0/24 (IETF protocol assignments)
  if (a === 0) return true; // "this network"
  return false;
}

/**
 * Extracts the embedded IPv4 address from an IPv4-mapped IPv6 literal in
 * EITHER the WHATWG-normalized hex form (`::ffff:7f00:1`, produced by `new
 * URL()`) or the dotted-quad form (`::ffff:127.0.0.1`, produced by DNS
 * resolution). Returns undefined if `ip` isn't an IPv4-mapped address.
 */
function extractIPv4MappedAddress(ipLower: string): string | undefined {
  const m = /^::ffff:([0-9a-f:.]+)$/.exec(ipLower);
  if (!m) return undefined;
  const rest = m[1] as string;
  if (net.isIPv4(rest)) return rest;
  const hx = rest.split(":");
  if (hx.length === 2) {
    const hi = parseInt(hx[0] as string, 16);
    const lo = parseInt(hx[1] as string, 16);
    if (Number.isFinite(hi) && Number.isFinite(lo)) {
      return `${(hi >> 8) & 255}.${hi & 255}.${(lo >> 8) & 255}.${lo & 255}`;
    }
  }
  return undefined;
}

function isPrivateOrLocalIPv6(ip: string): boolean {
  const normalized = ip.toLowerCase();
  if (normalized === "::1") return true; // loopback
  if (normalized === "::") return true; // unspecified
  if (/^fe[89ab]/.test(normalized)) return true; // link-local fe80::/10
  if (normalized.startsWith("fc") || normalized.startsWith("fd")) return true; // unique local fc00::/7
  const mapped = extractIPv4MappedAddress(normalized);
  if (mapped !== undefined) return isPrivateOrLocalIPv4(mapped);
  return false;
}

function isPrivateOrLocalIP(ip: string): boolean {
  if (net.isIPv4(ip)) return isPrivateOrLocalIPv4(ip);
  if (net.isIPv6(ip)) return isPrivateOrLocalIPv6(ip);
  return false;
}

/**
 * Builds a `lookup` function for http(s).request that revalidates every
 * resolved IP against the SSRF blocklist unless allowLocal is set.
 *
 * Node >=20 enables `autoSelectFamily` (Happy Eyeballs) by default, which
 * calls the custom `lookup` with `options.all = true` and expects the
 * callback to return an ARRAY of `{address, family}` entries instead of a
 * single address. This must honor that contract (and the `family`/`hints`/
 * `verbatim` options) rather than always requesting/returning a single
 * address, or every DNS-resolved (non-literal-IP) request fails with
 * "Invalid IP address: undefined" under default Node settings.
 */
function makeGuardedLookup(allowLocal: boolean): typeof dns.lookup {
  const guarded = ((hostname: string, options: unknown, callback: unknown) => {
    const hasOptions = typeof options !== "function";
    const cb = (hasOptions ? callback : options) as (
      err: NodeJS.ErrnoException | null,
      address: string | dns.LookupAddress[],
      family?: number
    ) => void;
    const lookupOptions = (hasOptions ? options : {}) as dns.LookupAllOptions | dns.LookupOneOptions;

    const blocked = () => {
      const blockErr = new Error("SSRF guard: refusing to connect to private/local address") as NodeJS.ErrnoException;
      blockErr.code = "SSRF_BLOCKED";
      return blockErr;
    };

    if ((lookupOptions as dns.LookupAllOptions).all) {
      dns.lookup(hostname, lookupOptions as dns.LookupAllOptions, (err, addresses) => {
        if (err) return cb(err, [], undefined);
        if (!allowLocal && addresses.some((entry) => isPrivateOrLocalIP(entry.address))) {
          return cb(blocked(), [], undefined);
        }
        return cb(null, addresses, undefined);
      });
      return;
    }

    dns.lookup(hostname, lookupOptions as dns.LookupOneOptions, (err, address, family) => {
      if (err) return cb(err, "", 0);
      if (!allowLocal && isPrivateOrLocalIP(address)) {
        return cb(blocked(), "", 0);
      }
      return cb(null, address, family);
    });
  }) as unknown as typeof dns.lookup;
  return guarded;
}

/** Test-only surface for exercising internals not otherwise reachable deterministically without a network. */
export const __testables = { makeGuardedLookup };

function detectChallenge(bodyLower: string): boolean {
  return CHALLENGE_SIGNATURES.some((sig) => bodyLower.includes(sig));
}

function decodeWithMojibakeCheck(buf: Buffer): { text: string; ratio: number } {
  const text = buf.toString("utf-8");
  const replacementCount = (text.match(/�/g) ?? []).length;
  const ratio = text.length > 0 ? replacementCount / text.length : 0;
  return { text, ratio };
}

function looksLikeHtml(contentType: string, sample: string): boolean {
  if (contentType && /text\/html|application\/xhtml/i.test(contentType)) return true;
  if (contentType && contentType.length > 0) return false; // explicit non-html content-type
  // No content-type header at all — sniff for html-ish markers.
  return /<html[\s>]|<!doctype html/i.test(sample);
}

function singleRequest(
  targetUrl: URL,
  timeoutMs: number,
  maxBytes: number,
  allowLocal: boolean
): Promise<{ status: number; headers: http.IncomingHttpHeaders; body: Buffer; truncated: boolean }> {
  return new Promise((resolve, reject) => {
    const lib = targetUrl.protocol === "https:" ? https : http;
    const req = lib.request(
      targetUrl,
      {
        method: "GET",
        timeout: timeoutMs,
        lookup: makeGuardedLookup(allowLocal),
        headers: { "user-agent": "web-copy-analyzer/0.1 (+local-fetch)" },
      },
      (res) => {
        const chunks: Buffer[] = [];
        let received = 0;
        let truncated = false;
        res.on("data", (chunk: Buffer) => {
          if (received >= maxBytes) {
            truncated = true;
            return;
          }
          const remaining = maxBytes - received;
          const slice = chunk.length > remaining ? chunk.subarray(0, remaining) : chunk;
          chunks.push(slice);
          received += slice.length;
          if (chunk.length > remaining) truncated = true;
        });
        res.on("end", () => {
          resolve({ status: res.statusCode ?? 0, headers: res.headers, body: Buffer.concat(chunks), truncated });
        });
        res.on("error", reject);
      }
    );
    req.on("timeout", () => {
      req.destroy(new Error("TIMEOUT"));
    });
    req.on("error", (err: NodeJS.ErrnoException) => reject(err));
    req.end();
  });
}

export async function fetchPage(options: FetchPageOptions): Promise<FetchResult> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const maxBytes = options.maxBytes ?? DEFAULT_MAX_BYTES;
  const allowLocal = options.allowLocal ?? false;

  if (timeoutMs < MIN_TIMEOUT_MS || timeoutMs > MAX_TIMEOUT_MS) {
    throw new FetchPageValidationError(`timeout_ms must be within [${MIN_TIMEOUT_MS}, ${MAX_TIMEOUT_MS}]`);
  }
  if (!/^https?:\/\//i.test(options.url)) {
    throw new FetchPageValidationError("url must start with http:// or https://");
  }

  let currentUrl: URL;
  try {
    currentUrl = new URL(options.url);
  } catch {
    return { ok: false, status: 0, finalUrl: options.url, contentType: "", bytes: 0, html: "", error: "invalid url", errorKind: "network" };
  }

  const visited = new Set<string>();

  for (let redirectCount = 0; redirectCount <= MAX_REDIRECTS; redirectCount++) {
    const key = currentUrl.toString();
    if (visited.has(key)) {
      return {
        ok: false,
        status: 0,
        finalUrl: key,
        contentType: "",
        bytes: 0,
        html: "",
        error: "redirect loop detected",
        errorKind: "network",
      };
    }
    visited.add(key);

    // literal-IP hosts (e.g. "http://127.0.0.1/" or "http://169.254.169.254/")
    // never invoke the custom `lookup` function below — Node skips DNS
    // resolution entirely when the hostname is already an IP address — so
    // the SSRF check must also run synchronously against the literal host
    // before attempting the connection.
    const literalHost = currentUrl.hostname.replace(/^\[|\]$/g, ""); // strip IPv6 brackets
    if (!allowLocal && net.isIP(literalHost) !== 0 && isPrivateOrLocalIP(literalHost)) {
      return {
        ok: false,
        status: 0,
        finalUrl: key,
        contentType: "",
        bytes: 0,
        html: "",
        error: `SSRF guard: refusing to connect to private/local address ${literalHost}`,
        errorKind: "blocked",
      };
    }

    let response;
    try {
      response = await singleRequest(currentUrl, timeoutMs, maxBytes, allowLocal);
    } catch (err) {
      const nodeErr = err as NodeJS.ErrnoException;
      if (nodeErr.code === "SSRF_BLOCKED") {
        return {
          ok: false,
          status: 0,
          finalUrl: key,
          contentType: "",
          bytes: 0,
          html: "",
          error: nodeErr.message,
          errorKind: "blocked",
        };
      }
      if (nodeErr.message === "TIMEOUT" || nodeErr.code === "ETIMEDOUT") {
        return { ok: false, status: 0, finalUrl: key, contentType: "", bytes: 0, html: "", error: "timeout", errorKind: "timeout" };
      }
      return {
        ok: false,
        status: 0,
        finalUrl: key,
        contentType: "",
        bytes: 0,
        html: "",
        error: nodeErr.message ?? "network error",
        errorKind: "network",
      };
    }

    if (response.status >= 300 && response.status < 400 && response.headers.location) {
      if (redirectCount === MAX_REDIRECTS) {
        return {
          ok: false,
          status: response.status,
          finalUrl: key,
          contentType: "",
          bytes: 0,
          html: "",
          error: "too many redirects",
          errorKind: "network",
        };
      }
      currentUrl = new URL(response.headers.location, currentUrl);
      continue;
    }

    const contentType = String(response.headers["content-type"] ?? "");
    const { text, ratio } = decodeWithMojibakeCheck(response.body);

    if (response.status === 404) {
      return {
        ok: false,
        status: 404,
        finalUrl: key,
        contentType,
        bytes: response.body.length,
        html: "",
        error: "not found",
        errorKind: "not_found",
      };
    }

    const challengeDetected = detectChallenge(text.toLowerCase());
    if (response.status === 403 || response.status === 429 || challengeDetected) {
      return {
        ok: false,
        status: response.status,
        finalUrl: key,
        contentType,
        bytes: response.body.length,
        html: "",
        error: "blocked (bot challenge or forbidden)",
        errorKind: "blocked",
        challengeDetected,
      };
    }

    if (!looksLikeHtml(contentType, text.slice(0, 512))) {
      return {
        ok: false,
        status: response.status,
        finalUrl: key,
        contentType,
        bytes: response.body.length,
        html: "",
        error: `non-html content-type: ${contentType || "unknown"}`,
        errorKind: "non_html",
      };
    }

    return {
      ok: true,
      status: response.status,
      finalUrl: key,
      contentType,
      bytes: response.body.length,
      html: text,
      errorKind: response.truncated ? "too_large" : "ok",
      mojibakeRatio: ratio,
      truncated: response.truncated,
      ...(ratio > MOJIBAKE_RATIO_THRESHOLD ? { error: "possible encoding mismatch (mojibake)" } : {}),
    };
  }

  return {
    ok: false,
    status: 0,
    finalUrl: currentUrl.toString(),
    contentType: "",
    bytes: 0,
    html: "",
    error: "too many redirects",
    errorKind: "network",
  };
}
