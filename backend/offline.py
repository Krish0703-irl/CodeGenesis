"""Rule-based lesson planner used when no AI provider is configured or the AI call fails."""

import random
import re

MAX_CHUNK_LINES = 25

COMMENT_PREFIXES = ("//", "#", "/*", "*", "--")


def _brace_delta(line: str) -> int:
    # Ignore braces inside string/char literals and line comments
    stripped = re.sub(r'"(\\.|[^"\\])*"|\'(\\.|[^\'\\])*\'', "", line)
    stripped = stripped.split("//", 1)[0]
    return stripped.count("{") - stripped.count("}")


def _is_blank(line: str) -> bool:
    return not line.strip()


def split_into_chunks(lines: list[str], language: str) -> list[int]:
    """Return 1-based start lines of top-level chunks."""
    starts: list[int] = []
    depth = 0
    previous_blank = True

    for index, line in enumerate(lines):
        line_number = index + 1
        if _is_blank(line):
            previous_blank = True
            continue

        top_level = depth == 0 and (language != "python" or not line[:1].isspace())
        if top_level and (previous_blank or not starts):
            starts.append(line_number)

        if language != "python":
            depth = max(0, depth + _brace_delta(line))
        previous_blank = False

    if not starts:
        return [1]
    starts[0] = 1
    return _split_long_chunks(lines, starts)


def _split_long_chunks(lines: list[str], starts: list[int]) -> list[int]:
    """Break very long chunks (e.g. a big main) at blank lines inside them."""
    result: list[int] = []
    bounds = starts + [len(lines) + 1]
    for start, next_start in zip(bounds, bounds[1:]):
        result.append(start)
        if next_start - start <= MAX_CHUNK_LINES:
            continue
        last_split = start
        for line_number in range(start + 1, next_start):
            previous = lines[line_number - 2]
            current = lines[line_number - 1]
            if (
                _is_blank(previous)
                and not _is_blank(current)
                and line_number - last_split >= 4
                and next_start - line_number >= 3
            ):
                result.append(line_number)
                last_split = line_number
    return result


def _leading_comment(chunk: list[str]) -> str:
    comments = []
    for line in chunk:
        text = line.strip()
        if not text:
            continue
        if text.startswith(COMMENT_PREFIXES) and not text.startswith(("#include", "#define")):
            comments.append(text.lstrip("/#*- ").rstrip("*/ ").strip())
        else:
            break
    return " ".join(c for c in comments if c)


def describe_chunk(chunk: list[str], language: str) -> tuple[str, str]:
    """Guess a title and explanation for a chunk of code."""
    code_lines = [l.strip() for l in chunk if l.strip()]
    comment = _leading_comment(chunk)
    first = next(
        (l for l in code_lines if not l.startswith(COMMENT_PREFIXES) or l.startswith(("#include", "#define"))),
        code_lines[0] if code_lines else "",
    )

    if first.startswith("#include") or first.startswith(("import ", "from ")) or first.startswith("using namespace"):
        libraries = [
            m.group(1)
            for l in code_lines
            for m in [re.match(r"#include\s*[<\"]([^>\"]+)[>\"]|import\s+([\w.]+)|from\s+([\w.]+)", l)]
            if m and m.group(1)
        ]
        title = "Bring in the libraries we need"
        explanation = (
            "Every program starts by pulling in the tools it depends on. "
            + (f"Here we include {', '.join(libraries)}, " if libraries else "These lines load the libraries ")
            + "so the rest of the code can use what they provide."
        )
        if any(l.startswith("using namespace") for l in code_lines):
            explanation += " The 'using namespace' line lets us write names like cout without the std:: prefix."
    elif match := re.match(r"(?:class|struct)\s+(\w+)", first):
        name = match.group(1)
        title = f"Define the {name} type"
        explanation = (
            f"We create a {first.split()[0]} called {name}. It groups together the data "
            "(fields) and behaviour (methods) that belong to one idea in the program."
        )
    elif match := re.match(r"def\s+(\w+)\s*\(", first):
        name = match.group(1)
        title = f"Write the {name} function"
        explanation = (
            f"The function {name} packages one job into a reusable piece. "
            "Read its parameters to see what it needs, and its return value to see what it gives back."
        )
    elif re.match(r"(int|void)\s+main\s*\(", first) or first.startswith("if __name__"):
        title = "Write the main entry point"
        explanation = (
            "This is where the program actually starts running. It uses the pieces we built "
            "earlier, step by step, to produce the final result."
        )
    elif match := re.match(r"[\w:<>,\s\*&]+?\b(\w+)\s*\([^;]*\)\s*(const)?\s*\{?$", first):
        name = match.group(1)
        title = f"Write the {name} function"
        explanation = (
            f"The function {name} handles one focused task. Splitting work into functions keeps "
            "the program readable and lets us reuse the logic."
        )
    elif first.startswith("#define") or re.match(r"(const|constexpr|static)\b", first):
        title = "Set up constants"
        explanation = "These values are fixed for the whole program, so we give them names once and reuse them."
    else:
        title = "Continue building the logic"
        explanation = "This part adds the next piece of logic. Read it line by line and connect it to what came before."

    if comment:
        explanation = f"{comment}. {explanation}" if not comment.endswith(".") else f"{comment} {explanation}"
    return title, explanation


def make_quizzes(titles: list[str], seed: str) -> list[dict | None]:
    """Make one 'which step is this?' question per step from the other step titles."""
    unique = list(dict.fromkeys(titles))
    if len(unique) < 2:
        return [None] * len(titles)

    rng = random.Random(seed)
    quizzes: list[dict | None] = []
    for title in titles:
        distractors = [t for t in unique if t != title]
        rng.shuffle(distractors)
        options = [title] + distractors[:3]
        rng.shuffle(options)
        quizzes.append(
            {
                "question": "Which description best matches the code added in this step?",
                "options": options,
                "answer_index": options.index(title),
                "explanation": f"This step's job is: {title.lower()}.",
            }
        )
    return quizzes


def plan_lesson(code: str, language: str) -> dict:
    lines = code.splitlines()
    starts = split_into_chunks(lines, language)
    bounds = starts + [len(lines) + 1]

    steps = []
    for start, next_start in zip(bounds, bounds[1:]):
        title, explanation = describe_chunk(lines[start - 1 : next_start - 1], language)
        steps.append({"title": title, "explanation": explanation, "start_line": start})

    for step, quiz in zip(steps, make_quizzes([s["title"] for s in steps], code)):
        step["quiz"] = quiz

    return {
        "title": "Rebuilding your program",
        "summary": f"We'll rebuild this program in {len(steps)} steps, explaining why each part exists.",
        "steps": steps,
    }
