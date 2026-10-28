export const API_URL: string =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export type Language = "cpp" | "c" | "python" | "java" | "javascript" | "other";

export type Quiz = {
  question: string;
  options: string[];
  answer_index: number;
  explanation: string;
};

export type Step = {
  title: string;
  explanation: string;
  code: string;
  start_line: number;
  end_line: number;
  quiz: Quiz | null;
};

export type Lesson = {
  title: string;
  summary: string;
  language: Language;
  source: "ai" | "offline";
  provider: string | null;
  warning: string | null;
  steps: Step[];
};

export type Health = {
  status: string;
  ai_enabled: boolean;
  provider: string | null;
};

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d: { msg: string }) => d.msg).join(", ");
    }
  } catch {
    // fall through to the status text
  }
  return `${response.status} ${response.statusText}`;
}

export async function generateLesson(
  code: string,
  language: Language,
): Promise<Lesson> {
  const response = await fetch(`${API_URL}/generate-lesson`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language }),
  });
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function getHealth(): Promise<Health> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}
