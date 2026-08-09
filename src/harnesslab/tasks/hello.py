"""A hello-world evaluation, to prove the framework is wired up end to end.

Deliberately trivial and deliberately *not* part of any suite: it exists so
Day 1 can demonstrate that a model string resolves, a task runs, a scorer fires,
and a readable `.eval` log lands on disk. It uses `includes()` rather than the
project's real scorers because those need the environment generator (SPEC-002),
which does not exist yet.

    uv run inspect eval src/harnesslab/tasks/hello.py --model groq/llama-3.1-8b-instant
"""

from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import includes
from inspect_ai.solver import generate


@task
def hello() -> Task:
    """Three questions with unambiguous one-word answers.

    Answers are checked by substring, so this measures "the pipeline works",
    not capability. Nothing here should ever be cited as a result.
    """
    return Task(
        dataset=[
            Sample(
                input="What is the capital of France? Reply with the city name only.",
                target="Paris",
            ),
            Sample(
                input="What is 17 + 25? Reply with the number only.",
                target="42",
            ),
            Sample(
                input="Which planet is closest to the Sun? Reply with the name only.",
                target="Mercury",
            ),
        ],
        solver=generate(),
        scorer=includes(),
    )
