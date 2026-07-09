import { test } from "node:test";
import assert from "node:assert/strict";
import * as http from "node:http";
import type { AddressInfo } from "node:net";
import { fetchPage, __testables } from "../fetch-node.js";

function startServer(handler: http.RequestListener): Promise<{ url: string; close: () => Promise<void> }> {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address() as AddressInfo;
      resolve({
        url: `http://127.0.0.1:${port}`,
        close: () => new Promise((res) => server.close(() => res())),
      });
    });
  });
}

test("fetchPage: 문제표 SSRF guard — loopback target blocked by default (allow_local=false)", async () => {
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<html><body><h1>hi</h1></body></html>");
  });
  try {
    const result = await fetchPage({ url });
    assert.equal(result.ok, false);
    assert.equal(result.errorKind, "blocked");
  } finally {
    await close();
  }
});

test("fetchPage: SSRF guard — allow_local=true permits loopback fetch", async () => {
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<html><body><h1>hi there</h1></body></html>");
  });
  try {
    const result = await fetchPage({ url, allowLocal: true });
    assert.equal(result.ok, true);
    assert.equal(result.status, 200);
    assert.ok(result.html.includes("hi there"));
  } finally {
    await close();
  }
});

test("fetchPage: 문제표 #1 — 404 maps to error_kind not_found", async () => {
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(404, { "content-type": "text/html" });
    res.end("not found");
  });
  try {
    const result = await fetchPage({ url, allowLocal: true });
    assert.equal(result.ok, false);
    assert.equal(result.errorKind, "not_found");
  } finally {
    await close();
  }
});

test("fetchPage: 문제표 #3 — challenge signature in body maps to error_kind blocked", async () => {
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<html><body>Just a moment... checking your browser</body></html>");
  });
  try {
    const result = await fetchPage({ url, allowLocal: true });
    assert.equal(result.ok, false);
    assert.equal(result.errorKind, "blocked");
    assert.equal(result.challengeDetected, true);
  } finally {
    await close();
  }
});

test("fetchPage: 문제표 #3 — 403 status alone maps to error_kind blocked", async () => {
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(403, { "content-type": "text/html" });
    res.end("Forbidden");
  });
  try {
    const result = await fetchPage({ url, allowLocal: true });
    assert.equal(result.ok, false);
    assert.equal(result.errorKind, "blocked");
  } finally {
    await close();
  }
});

test("fetchPage: 문제표 #16 — non-HTML content-type maps to error_kind non_html", async () => {
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(200, { "content-type": "application/pdf" });
    res.end("%PDF-1.4 fake pdf bytes");
  });
  try {
    const result = await fetchPage({ url, allowLocal: true });
    assert.equal(result.ok, false);
    assert.equal(result.errorKind, "non_html");
  } finally {
    await close();
  }
});

test("fetchPage: 문제표 #17 — redirect loop (self-redirect) maps to error_kind network", async () => {
  const { url, close } = await startServer((req, res) => {
    res.writeHead(302, { location: req.url === "/" ? url + "/" : url });
    res.end();
  });
  try {
    const result = await fetchPage({ url, allowLocal: true });
    assert.equal(result.ok, false);
    assert.equal(result.errorKind, "network");
  } finally {
    await close();
  }
});

test("fetchPage: timeout — slow server maps to error_kind timeout", async () => {
  const { url, close } = await startServer((_req, res) => {
    // Never respond within the timeout window.
    setTimeout(() => {
      res.writeHead(200, { "content-type": "text/html" });
      res.end("<html><body>too slow</body></html>");
    }, 5000);
  });
  try {
    const result = await fetchPage({ url, allowLocal: true, timeoutMs: 1000 });
    assert.equal(result.ok, false);
    assert.equal(result.errorKind, "timeout");
  } finally {
    await close();
  }
});

test("fetchPage: 문제표 #5 — oversized page is truncated to max_bytes, error_kind too_large", async () => {
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<html><body>" + "a".repeat(10_000) + "</body></html>");
  });
  try {
    const result = await fetchPage({ url, allowLocal: true, maxBytes: 100 });
    assert.equal(result.ok, true);
    assert.equal(result.errorKind, "too_large");
    assert.equal(result.truncated, true);
    assert.ok(result.bytes <= 100);
  } finally {
    await close();
  }
});

test("fetchPage: rejects timeout_ms outside the [1000, 30000] schema range", async () => {
  await assert.rejects(() => fetchPage({ url: "http://127.0.0.1:1/", timeoutMs: 500 }));
  await assert.rejects(() => fetchPage({ url: "http://127.0.0.1:1/", timeoutMs: 40_000 }));
});

test("fetchPage: DNS-name host (not a literal IP) resolves via autoSelectFamily's options.all=true lookup path — reproduces the 'Invalid IP address: undefined' regression on Node >=20", async () => {
  // "localhost" is a DNS NAME, not a literal IP, so Node's http client invokes
  // the custom `lookup` (unlike literal IPs, which skip it entirely). With
  // autoSelectFamily on by default (Node >=20), that lookup is called with
  // options.all=true and must return an array of {address, family}. This is
  // the exact shape that was broken before the fix.
  const { url, close } = await startServer((_req, res) => {
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<html><body>hello via localhost</body></html>");
  });
  try {
    const port = new URL(url).port;
    const result = await fetchPage({ url: `http://localhost:${port}/`, allowLocal: true });
    assert.equal(result.ok, true);
    assert.equal(result.status, 200);
    assert.ok(result.html.includes("hello via localhost"));
  } finally {
    await close();
  }
});

test("makeGuardedLookup: options.all=true path still enforces the SSRF guard — a loopback resolution is blocked when allowLocal is false", async () => {
  const lookup = __testables.makeGuardedLookup(false);
  await new Promise<void>((resolve, reject) => {
    (lookup as unknown as (
      hostname: string,
      options: { all: true },
      cb: (err: NodeJS.ErrnoException | null, addresses: Array<{ address: string; family: number }>) => void
    ) => void)("localhost", { all: true }, (err, addresses) => {
      try {
        assert.ok(err, "expected SSRF_BLOCKED error for loopback resolution under options.all=true");
        assert.equal(err?.code, "SSRF_BLOCKED");
        assert.equal(addresses.length, 0);
        resolve();
      } catch (e) {
        reject(e);
      }
    });
  });
});

test("fetchPage: rejects non-http(s) scheme", async () => {
  await assert.rejects(() => fetchPage({ url: "ftp://example.com/file" }));
});

// --- IPv4-mapped IPv6 SSRF bypass (HIGH) ------------------------------------
// `new URL()` normalizes bracketed IPv4-mapped IPv6 literals to their hex
// form (`[::ffff:127.0.0.1]` -> host `::ffff:7f00:1`), which the blocklist
// must classify via the embedded IPv4 the same as the dotted-quad form.

test("fetchPage: SSRF guard blocks IPv4-mapped IPv6 loopback literal [::ffff:127.0.0.1]", async () => {
  const result = await fetchPage({ url: "http://[::ffff:127.0.0.1]/" });
  assert.equal(result.ok, false);
  assert.equal(result.errorKind, "blocked");
});

test("fetchPage: SSRF guard blocks IPv4-mapped IPv6 cloud-metadata literal [::ffff:169.254.169.254]", async () => {
  const result = await fetchPage({ url: "http://[::ffff:169.254.169.254]/" });
  assert.equal(result.ok, false);
  assert.equal(result.errorKind, "blocked");
});

test("fetchPage: SSRF guard blocks IPv4-mapped IPv6 RFC1918 literal [::ffff:10.0.0.1]", async () => {
  const result = await fetchPage({ url: "http://[::ffff:10.0.0.1]/" });
  assert.equal(result.ok, false);
  assert.equal(result.errorKind, "blocked");
});

test("fetchPage: SSRF guard blocks the unspecified IPv6 address [::]", async () => {
  const result = await fetchPage({ url: "http://[::]/" });
  assert.equal(result.ok, false);
  assert.equal(result.errorKind, "blocked");
});

test("fetchPage: SSRF guard blocks full fe80::/10 link-local range, not just the fe80: prefix ([febf::1])", async () => {
  const result = await fetchPage({ url: "http://[febf::1]/" });
  assert.equal(result.ok, false);
  assert.equal(result.errorKind, "blocked");
});

test("fetchPage: SSRF guard blocks CGNAT 100.64.0.0/10 (http://100.64.0.1/)", async () => {
  const result = await fetchPage({ url: "http://100.64.0.1/" });
  assert.equal(result.ok, false);
  assert.equal(result.errorKind, "blocked");
});

test("fetchPage: SSRF guard still blocks plain loopback and cloud-metadata literals (regression)", async () => {
  const loopback = await fetchPage({ url: "http://127.0.0.1/" });
  assert.equal(loopback.ok, false);
  assert.equal(loopback.errorKind, "blocked");

  const metadata = await fetchPage({ url: "http://169.254.169.254/" });
  assert.equal(metadata.ok, false);
  assert.equal(metadata.errorKind, "blocked");
});

test("fetchPage: a real public URL still succeeds (SSRF guard doesn't over-block)", async () => {
  const result = await fetchPage({ url: "https://example.com/" });
  assert.equal(result.ok, true);
  assert.equal(result.status, 200);
});
