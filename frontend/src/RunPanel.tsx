import { useState } from "react";

import { RUNNABLE, runCode, type Language, type RunResult } from "./api";

type Props = {
  code: string;
  language: Language;
};

export default function RunPanel({ code, language }: Props) {
  const [stdin, setStdin] = useState("");
  const [result, setResult] = useState<RunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  if (!RUNNABLE.includes(language)) {
    return <p className="saved-meta">Running code is available for C++, C and Python.</p>;
  }

  async function run() {
    setRunning(true);
    setError("");
    try {
      setResult(await runCode(code, language, stdin));
    } catch (err) {
      setResult(null);
      setError(
        err instanceof TypeError
          ? "Can't reach the backend. Is it running on port 8000?"
          : `Couldn't run the code: ${(err as Error).message}`,
      );
    } finally {
      setRunning(false);
    }
  }

  const failed = result && (result.timed_out || result.exit_code !== 0);

  function status(r: RunResult): string {
    if (r.timed_out) return "Stopped: took too long";
    if (r.exit_code === null) return "Could not run";
    if (r.exit_code === 0) return "Ran successfully";
    if (r.compile_output && !r.stdout && !r.stderr) return "Compile error";
    return `Exited with code ${r.exit_code}`;
  }

  return (
    <div className="run-panel">
      <label className="run-input">
        Program input (optional)
        <textarea
          value={stdin}
          onChange={(e) => setStdin(e.target.value)}
          rows={2}
          placeholder="Anything your program reads with cin / input()"
        />
      </label>
      <button className="run-button" onClick={run} disabled={running}>
        {running ? "Running…" : "▶ Run code"}
      </button>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="run-output">
          <p className={failed ? "run-status bad" : "run-status good"}>
            {status(result)}
          </p>
          {result.compile_output && <pre className="stderr">{result.compile_output}</pre>}
          {result.stdout && <pre>{result.stdout}</pre>}
          {result.stderr && <pre className="stderr">{result.stderr}</pre>}
          {!result.stdout && !result.stderr && !result.compile_output && (
            <pre className="muted">(no output)</pre>
          )}
        </div>
      )}
    </div>
  );
}
