import { useState } from "react";

import Home from "./Home";
import LessonPlayer from "./LessonPlayer";
import { deleteLesson, loadLessons, type SavedLesson } from "./storage";

function App() {
  const [savedLessons, setSavedLessons] = useState<SavedLesson[]>(loadLessons);
  const [active, setActive] = useState<SavedLesson | null>(null);

  function openLesson(saved: SavedLesson) {
    // Re-read so a lesson reopened from the list resumes its saved progress
    setActive(loadLessons().find((l) => l.id === saved.id) ?? saved);
  }

  function exitLesson() {
    setActive(null);
    setSavedLessons(loadLessons());
  }

  function removeLesson(id: string) {
    deleteLesson(id);
    setSavedLessons(loadLessons());
  }

  if (active) {
    return <LessonPlayer key={active.id} saved={active} onExit={exitLesson} />;
  }

  return <Home savedLessons={savedLessons} onOpen={openLesson} onDelete={removeLesson} />;
}

export default App;
