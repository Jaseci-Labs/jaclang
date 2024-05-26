from pydantic import BaseModel, Field
from enum import Enum
import dspy


llm = dspy.OllamaLocal(model="phi3")

dspy.settings.configure(lm = llm)

class Task(BaseModel):
    description: str = Field(description="The contents of the task")

class TaskFull(Task):
    time_to_spend: int = Field(description="Number of minutes one is expected to spend on this task")
    priority: int = Field(ge=0, le=10, description="The critical level of the task")

class PrioritySignature(dspy.Signature):
    """Estimate the priority of each task, score from 0 to 10 where 10 is the most critical"""

    input: Task = dspy.InputField()
    output: TaskFull = dspy.OutputField()

priorityPredictor = dspy.TypedPredictor(PrioritySignature)

tasks = [
        Task(description="Have some sleep"),
        Task(description="Enjoy a better weekend with my girlfriend"),
        Task(description="Work on Jaseci Project"),
        Task(description="Teach EECS 281 Students"),
        Task(description="Enjoy family time with my parents"),
        ]

priorities = []
for task in tasks:
    priority = priorityPredictor(input = task).output
    priorities.append(priority)
    print(priority)

print(priorities)
