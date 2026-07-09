/**
 * Filesystem helpers backing 문제표 #20 (write failure → session-only
 * fallback) and #21 (concurrent append → atomic + retry).
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

/**
 * Appends a line atomically. Node's `fs.promises.appendFile` with the
 * default 'a' flag opens the file with O_APPEND, which the POSIX kernel
 * guarantees is atomic for writes under PIPE_BUF (our lines are far under
 * that) even across concurrent processes/handles — this is what satisfies
 * 문제표 #21's "동시 실행 쓰기 충돌" requirement. We additionally retry a
 * few times on transient errors (e.g. ENOENT while the directory is being
 * created by a racing writer, EMFILE) before surfacing failure, per the
 * table's "재시도 실패 시만 표면화".
 */
export async function atomicAppendLine(filePath: string, line: string, retries = 3): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true, mode: 0o700 });
  let lastErr: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      await fs.appendFile(filePath, line.endsWith("\n") ? line : `${line}\n`, { flag: "a", encoding: "utf-8", mode: 0o600 });
      return;
    } catch (err) {
      lastErr = err;
      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 5 * (attempt + 1)));
        continue;
      }
    }
  }
  throw lastErr;
}

/** Read a file's full text, or undefined if it doesn't exist. Any other error (EACCES etc.) propagates. */
export async function readFileIfExists(filePath: string): Promise<string | undefined> {
  try {
    return await fs.readFile(filePath, "utf-8");
  } catch (err) {
    const code = (err as NodeJS.ErrnoException).code;
    if (code === "ENOENT") return undefined;
    throw err;
  }
}

export async function writeFileEnsuringDir(filePath: string, content: string): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true, mode: 0o700 });
  await fs.writeFile(filePath, content, { encoding: "utf-8", mode: 0o600 });
}

/** Errors that mean "the growth-layer storage location itself is unusable" (문제표 #20: EACCES/ENOSPC/EROFS/...). */
export function isStorageUnavailableError(err: unknown): boolean {
  const code = (err as NodeJS.ErrnoException | undefined)?.code;
  return code === "EACCES" || code === "ENOSPC" || code === "EROFS" || code === "EPERM";
}
