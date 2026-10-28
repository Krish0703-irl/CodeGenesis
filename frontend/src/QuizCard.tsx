import type { Quiz } from "./api";

type Props = {
  quiz: Quiz;
  answer: number | undefined;
  onAnswer: (index: number) => void;
};

export default function QuizCard({ quiz, answer, onAnswer }: Props) {
  const answered = answer !== undefined;
  const correct = answer === quiz.answer_index;

  return (
    <div className="quiz">
      <h3>Check your understanding</h3>
      <p>{quiz.question}</p>
      <div className="quiz-options">
        {quiz.options.map((option, index) => {
          let state = "";
          if (answered && index === quiz.answer_index) state = "correct";
          else if (answered && index === answer) state = "wrong";
          return (
            <button
              key={index}
              className={`quiz-option ${state}`}
              disabled={answered}
              onClick={() => onAnswer(index)}
            >
              {option}
            </button>
          );
        })}
      </div>
      {answered && (
        <p className={correct ? "feedback good" : "feedback bad"}>
          {correct ? "Correct! " : "Not quite. "}
          {quiz.explanation}
        </p>
      )}
    </div>
  );
}
