from pydantic import BaseModel, Field
from datetime import timedelta, datetime
import subprocess
import dspy
import tempfile


class Score:
    def overall(self) -> float:
        raise Exception("Wrong Call")


class Comparison:
    scoreA = Score()
    scoreB = Score()

    def __init__(self, scoreA, scoreB):
        self.scoreA = scoreA
        self.scoreB = scoreB

    def preferA(self):
        return self.scoreA.overall() > self.scoreB.overall()


class AIScore(BaseModel, Score):
    consistency: int = Field(
        ge=0, le=10, description="Evaluate whether the response answered the question"
    )
    correctness: int = Field(
        ge=0,
        le=10,
        description="Evaluate whether the response is in general correct, or how correct it is",
    )

    def overall(self):
        return (self.consistency + self.correctness) / 2


class FactScore(BaseModel, Score):
    correctness: bool = Field(description="Whether the response answered is correct")

    def overall(self):
        return 10 if self.correctness else 0


class RunnerScore(BaseModel, Score):
    elapsed: timedelta
    correctness: bool

    def overall(self):
        return 10 / self.elapsed.seconds if self.correctness else 0


class Evaluator:
    def __init__(self):
        self.scoreA = Score()
        self.scoreB = Score()

    def eval(self, responseA, responseB) -> Comparison:
        raise Exception("Wrong Call")


class AIEvaluator(Evaluator):
    def __init__(self, context: str):
        self.client = dspy.OllamaLocal(model="phi3")
        dspy.configure(lm=self.client)
        self.context = context
        super()

    class EvalSignature(dspy.Signature):
        """You are evaluating the responses of two similar language models. Please provide scores that can help us evaluate how well the models work. Please return the scores in order"""

        problem_context: str = dspy.InputField()
        responses: list[str] = dspy.InputField()
        scores: list[AIScore] = dspy.OutputField()

    def eval(self, responseA, responseB) -> Comparison:
        predictor = dspy.TypedPredictor(self.EvalSignature)
        scores = predictor(
            responses=[responseA, responseB], problem_context=self.context
        ).scores
        comparison = Comparison(scores[0], scores[1])
        return comparison


class RunnerEvaluator(Evaluator):
    def __init__(self, input: str, correct_output: str):
        self.input = input
        self.correct_output = correct_output
        super().__init__()

    def run(self, source: str, inputPath: str):
        start = datetime.now()
        with open(inputPath, "r") as input:
            result = subprocess.check_output(["python", str(source)], stdin=input).decode()
        delta = datetime.now() - start
        return result, delta

    def eval(self, responseA, responseB) -> Comparison:
        sourceA = tempfile.NamedTemporaryFile(delete=False)
        sourceB = tempfile.NamedTemporaryFile(delete=False)
        inputFile = tempfile.NamedTemporaryFile(delete=False)
        with sourceA, sourceB, inputFile:
            sourceA.write(responseA.encode())
            sourceB.write(responseB.encode())
            inputFile.write(self.input.encode())
        outputA, timeA = self.run(sourceA.name, inputFile.name)
        outputB, timeB = self.run(sourceB.name, inputFile.name)

        scoreA = RunnerScore(
            elapsed=timeA, correctness=(outputA == self.correct_output)
        )
        scoreB = RunnerScore(
            elapsed=timeB, correctness=(outputB == self.correct_output)
        )
        return Comparison(scoreA, scoreB)


class FactEvaluator(Evaluator):
    def __init__(self, answer: str):
        self.answer = answer
        super()

    def eval(self, responseA, responseB) -> Comparison:
        scoreA = FactScore(correctness=(responseA == self.answer))
        scoreB = FactScore(correctness=(responseB == self.answer))
        return Comparison(scoreA, scoreB)
