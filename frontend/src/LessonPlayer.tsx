import { useEffect, useRef, useState } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";

import QuizCard from "./QuizCard";
import { monacoLanguage } from "./samples";
import { emptyProgress, saveProgress, type Progress, type SavedLesson } from "./storage";
import { useSpeech } from "./useSpeech";

type EditorInstance = Parameters<OnMount>[0];
type MonacoInstance = Parameters<OnMount>[1];

const SPEEDS = { slow: 1, normal: 3, fast: 10 } as const;
type Speed = keyof typeof SPEEDS;

type Props = {
  saved: SavedLesson;
  onExit: () => void;
};

export default function LessonPlayer({ saved, onExit }: Props) {
  const { lesson } = saved;
  const steps = lesson.steps;
  const fullCode = steps.map((s) => s.code).join("\n");

  const [progress, setProgress] = useState<Progress>(saved.progress);
  const [stepIndex, setStepIndex] = useState(() =>
    Math.min(saved.progress.currentStep, steps.length),
  );
  const [typed, setTyped] = useState(() => {
    const index = Math.min(saved.progress.currentStep, steps.length - 1);
    return saved.progress.completed.includes(index) ? steps[index].code.length : 0;
  });
  const [started, setStarted] = useState(false);
  const [paused, setPaused] = useState(false);
  const [voiceOn, setVoiceOn] = useState(true);
  const [speed, setSpeed] = useState<Speed>("normal");
  const [copied, setCopied] = useState(false);
  const speech = useSpeech();

  const editorRef = useRef<EditorInstance | null>(null);
  const monacoRef = useRef<MonacoInstance | null>(null);
  const decorationsRef = useRef<ReturnType<EditorInstance["createDecorationsCollection"]> | null>(null);

  const finished = stepIndex >= steps.length;
  const step = finished ? null : steps[stepIndex];
  const stepLength = step?.code.length ?? 0;
  const typingDone = typed >= stepLength;

  const before = steps
    .slice(0, stepIndex)
    .map((s) => s.code)
    .join("\n");
  const value = finished
    ? fullCode
    : (stepIndex > 0 ? `${before}\n` : "") + (step?.code.slice(0, typed) ?? "");

  // Type the current step's code a few characters at a time
  useEffect(() => {
    if (!started || paused || typingDone || finished) return;
    const chars = SPEEDS[speed];
    const timer = setInterval(() => {
      setTyped((t) => Math.min(t + chars, stepLength));
    }, 25);
    return () => clearInterval(timer);
  }, [started, paused, typingDone, finished, speed, stepLength]);

  // Highlight the lines of the current step and keep the cursor in view
  useEffect(() => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco) return;
    const model = editor.getModel();
    if (!model) return;

    const lastLine = model.getLineCount();
    decorationsRef.current?.clear();
    if (step) {
      const firstLine = stepIndex > 0 ? before.split("\n").length + 1 : 1;
      decorationsRef.current = editor.createDecorationsCollection([
        {
          range: new monaco.Range(firstLine, 1, lastLine, 1),
          options: { isWholeLine: true, className: "current-step-line" },
        },
      ]);
    }
    editor.revealLineInCenterIfOutsideViewport(lastLine);
  }, [value, step, stepIndex, before]);

  const handleMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
  };

  function updateProgress(next: Progress) {
    setProgress(next);
    saveProgress(saved.id, next);
  }

  function narrate(index: number, voice = voiceOn) {
    const target = steps[index];
    if (voice && target) speech.speak(`${target.title}. ${target.explanation}`);
  }

  function goTo(index: number, base: Progress = progress) {
    speech.stop();
    setPaused(false);
    setStepIndex(index);
    const alreadyDone = index < steps.length && base.completed.includes(index);
    setTyped(alreadyDone ? steps[index].code.length : 0);
    updateProgress({ ...base, currentStep: index });
    narrate(index);
  }

  function withCompleted(base: Progress, index: number): Progress {
    if (base.completed.includes(index)) return base;
    return { ...base, completed: [...base.completed, index].sort((a, b) => a - b) };
  }

  function start() {
    setStarted(true);
    goTo(stepIndex);
  }

  function next() {
    const base = step && !step.quiz ? withCompleted(progress, stepIndex) : progress;
    goTo(stepIndex + 1, base);
  }

  function answer(choice: number) {
    updateProgress(
      withCompleted({ ...progress, answers: { ...progress.answers, [stepIndex]: choice } }, stepIndex),
    );
  }

  function restart() {
    goTo(0, emptyProgress());
  }

  function toggleVoice() {
    const on = !voiceOn;
    setVoiceOn(on);
    if (on) narrate(stepIndex, true);
    else speech.stop();
  }

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(fullCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  const quizSteps = steps.filter((s) => s.quiz);
  const correct = steps.filter(
    (s, i) => s.quiz && progress.answers[i] === s.quiz.answer_index,
  ).length;
  const percent = Math.round((progress.completed.length / steps.length) * 100);

  return (
    <div className="player">
      <header className="player-header">
        <button className="ghost" onClick={onExit}>
          ← Home
        </button>
        <div className="player-title">
          <h1>{lesson.title}</h1>
          <span className="saved-meta">
            {lesson.source === "ai" ? `AI lesson (${lesson.provider})` : "Offline lesson"}
          </span>
        </div>
        <div className="player-progress">
          <span className="progress">
            <span className="progress-fill" style={{ width: `${percent}%` }} />
          </span>
          <span className="saved-meta">
            {progress.completed.length}/{steps.length} steps
          </span>
        </div>
      </header>

      {lesson.warning && <p className="warning">{lesson.warning}</p>}

      <div className="player-body">
        <nav className="step-list" aria-label="Lesson steps">
          <ol>
            {steps.map((s, i) => (
              <li key={i}>
                <button
                  className={[
                    i === stepIndex ? "current" : "",
                    progress.completed.includes(i) ? "done" : "",
                  ].join(" ")}
                  onClick={() => {
                    setStarted(true);
                    goTo(i);
                  }}
                >
                  <span className="step-number">{progress.completed.includes(i) ? "✓" : i + 1}</span>
                  {s.title}
                </button>
              </li>
            ))}
          </ol>
        </nav>

        <main className="code-panel">
          <Editor
            height="100%"
            language={monacoLanguage(lesson.language)}
            value={value}
            onMount={handleMount}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 15,
              scrollBeyondLastLine: false,
              renderLineHighlight: "none",
            }}
          />
        </main>

        <section className="teacher-panel">
          {step ? (
            <>
              <p className="step-label">
                Step {stepIndex + 1} of {steps.length} · lines {step.start_line}–{step.end_line}
              </p>
              <h2>{step.title}</h2>
              <p className="explanation">{step.explanation}</p>

              <div className="controls">
                {!typingDone && (
                  <button onClick={() => setPaused((p) => !p)}>{paused ? "Resume" : "Pause"}</button>
                )}
                {!typingDone && <button onClick={() => setTyped(stepLength)}>Show all</button>}
                {speech.supported && (
                  <>
                    <button onClick={() => narrate(stepIndex, true)} disabled={!voiceOn}>
                      {speech.speaking ? "Speaking…" : "Replay voice"}
                    </button>
                    <button onClick={toggleVoice}>{voiceOn ? "Voice on" : "Voice off"}</button>
                  </>
                )}
                <label>
                  Typing{" "}
                  <select value={speed} onChange={(e) => setSpeed(e.target.value as Speed)}>
                    <option value="slow">Slow</option>
                    <option value="normal">Normal</option>
                    <option value="fast">Fast</option>
                  </select>
                </label>
              </div>

              {typingDone && step.quiz && (
                <QuizCard
                  key={stepIndex}
                  quiz={step.quiz}
                  answer={progress.answers[stepIndex]}
                  onAnswer={answer}
                />
              )}

              <div className="nav">
                <button onClick={() => goTo(stepIndex - 1)} disabled={stepIndex === 0}>
                  Previous
                </button>
                <button className="primary" onClick={next} disabled={!typingDone}>
                  {stepIndex === steps.length - 1 ? "Finish" : "Next step"}
                </button>
              </div>
            </>
          ) : (
            <div className="finished">
              <h2>Lesson complete!</h2>
              <p>{lesson.summary}</p>
              <p className="score">
                You finished {progress.completed.length} of {steps.length} steps
                {quizSteps.length > 0 && ` and got ${correct} of ${quizSteps.length} questions right`}.
              </p>
              <div className="nav">
                <button onClick={copyCode}>{copied ? "Copied!" : "Copy code"}</button>
                <button onClick={restart}>Restart lesson</button>
                <button className="primary" onClick={onExit}>
                  Back home
                </button>
              </div>
            </div>
          )}
        </section>
      </div>

      {!started && (
        <div className="overlay">
          <div className="overlay-card">
            <h2>{lesson.title}</h2>
            <p>{lesson.summary}</p>
            <p className="saved-meta">
              {steps.length} steps · the code types itself while your teacher explains each part
            </p>
            <button className="primary" onClick={start}>
              {saved.progress.completed.length > 0 && !finished ? "Continue lesson" : "Start lesson"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
