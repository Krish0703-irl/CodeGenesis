import type { Lesson } from "./api";

export type Progress = {
  currentStep: number;
  completed: number[];
  answers: Record<number, number>;
};

export type SavedLesson = {
  id: string;
  code: string;
  lesson: Lesson;
  createdAt: number;
  progress: Progress;
};

const STORAGE_KEY = "codegenesis.lessons";
const MAX_SAVED = 20;

export function emptyProgress(): Progress {
  return { currentStep: 0, completed: [], answers: {} };
}

export function lessonId(code: string, language: string): string {
  let hash = 5381;
  const text = `${language}\n${code}`;
  for (let i = 0; i < text.length; i++) {
    hash = ((hash << 5) + hash + text.charCodeAt(i)) | 0;
  }
  return `l${(hash >>> 0).toString(36)}`;
}

export function loadLessons(): SavedLesson[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeLessons(lessons: SavedLesson[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(lessons.slice(0, MAX_SAVED)));
  } catch {
    // storage full or blocked: progress just won't persist
  }
}

export function saveLesson(saved: SavedLesson) {
  const others = loadLessons().filter((l) => l.id !== saved.id);
  writeLessons([saved, ...others]);
}

export function saveProgress(id: string, progress: Progress) {
  const lessons = loadLessons();
  const index = lessons.findIndex((l) => l.id === id);
  if (index === -1) return;
  lessons[index] = { ...lessons[index], progress };
  writeLessons(lessons);
}

export function deleteLesson(id: string) {
  writeLessons(loadLessons().filter((l) => l.id !== id));
}

export function percentComplete(saved: SavedLesson): number {
  const total = saved.lesson.steps.length;
  return total ? Math.round((saved.progress.completed.length / total) * 100) : 0;
}
