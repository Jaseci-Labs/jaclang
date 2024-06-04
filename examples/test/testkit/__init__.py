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
    value: int
    def overall(self):
        return self.value


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


class Input(BaseModel):
    responseA: str = Field(description="response from model A")
    responseB: str = Field(description="response from model B")


class Output(BaseModel):
    scoreA: int = Field(ge=0, le=10, description="preference of A over B")
    scoreB: int = Field(ge=0, le=10, description="preference of B over A")

class AIEvaluator(Evaluator):
    def __init__(self, context: str, correct_answer: str):
        self.client = dspy.OllamaLocal(
            base_url="http://52.23.242.52:11343", model="phi3", max_tokens=4000
        )
        dspy.configure(lm=self.client)
        self.context = context
        self.correct_answer = correct_answer
        super().__init__()

    class EvalSignature(dspy.Signature):
        """You are evaluating the responses of two similar language models. Please provide scores that can help us evaluate how well the models work. Please return the scores in order. The correct answer is given"""

        problem_context: str = dspy.InputField()
        correct_answer: str = dspy.InputField()
        responses: Input = dspy.InputField()
        scores: Output = dspy.OutputField()

    def eval(self, responseA, responseB) -> Comparison:
        predictor = dspy.TypedPredictor(self.EvalSignature)
        scores = predictor(
            responses=Input(responseA=responseA, responseB=responseB),
            problem_context=self.context,
            correct_answer=self.correct_answer,
        )
        scoreA = AIScore(value = scores.scores.scoreA)
        scoreB = AIScore(value = scores.scores.scoreB)
        comparison = Comparison(scoreA, scoreB)
        return comparison


class RunnerEvaluator(Evaluator):
    def __init__(self, input: str, correct_output: str):
        self.input = input
        self.correct_output = correct_output
        super().__init__()

    def run(self, source: str, inputPath: str):
        start = datetime.now()
        with open(inputPath, "r") as input:
            result = subprocess.check_output(
                ["python", str(source)], stdin=input
            ).decode()
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
