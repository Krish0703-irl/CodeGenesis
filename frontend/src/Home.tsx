import { useEffect, useState } from "react";
import Editor from "@monaco-editor/react";

import { generateLesson, getHealth, type Health, type Language } from "./api";
import RunPanel from "./RunPanel";
import { LANGUAGES, SAMPLES, monacoLanguage } from "./samples";
import {
  emptyProgress,
  lessonId,
  percentComplete,
  saveLesson,
  type SavedLesson,
} from "./storage";

type Props = {
  savedLessons: SavedLesson[];
  onOpen: (saved: SavedLesson) => void;
  onDelete: (id: string) => void;
};

export default function Home({ savedLessons, onOpen, onDelete }: Props) {
  const [code, setCode] = useState(SAMPLES[0].code);
  const [language, setLanguage] = useState<Language>(SAMPLES[0].language);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [backendDown, setBackendDown] = useState(false);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setBackendDown(true));
  }, []);

  async function teach() {
    if (!code.trim()) {
      setError("Paste some code first.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const lesson = await generateLesson(code, language);
      const saved: SavedLesson = {
        id: lessonId(code, language),
        code,
        lesson,
        createdAt: Date.now(),
        progress: emptyProgress(),
      };
      saveLesson(saved);
      onOpen(saved);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Can't reach the backend. Is it running on port 8000?"
          : `Couldn't build the lesson: ${(err as Error).message}`,
      );
    } finally {
      setLoading(false);
    }
  }

  function loadSample(index: number) {
    setCode(SAMPLES[index].code);
    setLanguage(SAMPLES[index].language);
  }

  return (
    <div className="home">
      <header className="home-header">
        <h1>CodeGenesis</h1>
        <p className="tagline">From finished code to understanding</p>
        <p className="status">
          {backendDown && <span className="badge badge-bad">Backend offline</span>}
          {health && (
            <span className={`badge ${health.ai_enabled ? "badge-good" : "badge-warn"}`}>
              {health.ai_enabled
                ? `AI teacher: ${health.provider === "nvidia" ? "NVIDIA" : "Gemini"}`
                : "Offline teacher (add an API key for AI lessons)"}
            </span>
          )}
        </p>
      </header>

      <section className="card">
        <div className="toolbar">
          <label>
            Language{" "}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as Language)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </label>
          <span className="spacer" />
          {SAMPLES.map((sample, index) => (
            <button key={sample.label} className="ghost" onClick={() => loadSample(index)}>
              {sample.label}
            </button>
          ))}
          <button className="ghost" onClick={() => setCode("")}>
            Clear
          </button>
        </div>

        <Editor
          height="440px"
          language={monacoLanguage(language)}
          value={code}
          onChange={(value) => setCode(value ?? "")}
          theme="vs-dark"
          options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false }}
        />

        <div className="actions">
          <button className="primary" onClick={teach} disabled={loading}>
            {loading ? "Building your lesson…" : "Teach Me This"}
          </button>
          {error && <p className="error">{error}</p>}
        </div>

        <RunPanel code={code} language={language} />
      </section>

      {savedLessons.length > 0 && (
        <section className="card">
          <h2>Your lessons</h2>
          <ul className="saved-list">
            {savedLessons.map((saved) => {
              const percent = percentComplete(saved);
              return (
                <li key={saved.id}>
                  <button className="saved-open" onClick={() => onOpen(saved)}>
                    <span className="saved-title">{saved.lesson.title}</span>
                    <span className="saved-meta">
                      {saved.lesson.steps.length} steps ·{" "}
                      {new Date(saved.createdAt).toLocaleDateString()}
                    </span>
                    <span className="progress">
                      <span className="progress-fill" style={{ width: `${percent}%` }} />
                    </span>
                    <span className="saved-meta">{percent}% complete</span>
                  </button>
                  <button
                    className="ghost danger"
                    aria-label={`Delete ${saved.lesson.title}`}
                    onClick={() => onDelete(saved.id)}
                  >
                    Delete
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
