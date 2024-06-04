from pprint import pprint

from datasets.arrow_dataset import tempfile
from testkit import AIEvaluator, RunnerEvaluator
from datasets import load_dataset

# gpt4eval = AIEvaluator("What is the answer to 1+1")
#
# eval = gpt4eval.eval("1.99998", "1+1")
# print(eval.preferA())
# print(eval.scoreA)
# print(eval.scoreB)


# ds = load_dataset("codeparrot/apps", split="test")
# iter = ds.iter(batch_size=1)
# for i in iter:
#     sample = {}
#     sample['question'] = i['question'][0]
#     sample['solution'] = json.loads(i['solutions'][0])[0]
#     sample['inputs'] = json.loads(i['input_output'][0])['inputs']
#     sample['outputs'] = json.loads(i['input_output'][0])['outputs']
#     pprint(sample)

# runnereval = RunnerEvaluator(input = "", correct_output="H\n")
# eval = runnereval.eval(responseA="print(\'H\')", responseB="print(\'M\')")
# print(eval.scoreA)
# print(eval.scoreB)

import subprocess


def codeRun(cmd: list[str], input: str):
    with open("/tmp/STDIN.txt", "w") as inputFile:
        inputFile.write(input)
    with open("/tmp/STDIN.txt", "r") as inputFile:
        return subprocess.check_output(cmd, stdin=inputFile).decode()


ds = load_dataset("rajpurkar/squad", split="validation")
iter = ds.iter(batch_size=1)
for i in iter:
    # question = " ".join(i['context'] + i['question'])
    question = f"{i['context'][0]} {i['question'][0]}"
    answer = " ".join(i["answers"][0]["text"])
    print(question, answer)
    aieval = AIEvaluator(question, correct_answer=answer)
    dspyResponse = codeRun(["python", "tested_code/qa/dspy_impl.py"], input = question)
    jacResponse = codeRun(["jac", "run", "tested_code/qa/jac_impl.jac"], input = question)
    print("DSPY Response", dspyResponse)
    print("JAC Response", jacResponse)
    comparison = aieval.eval(responseA= dspyResponse, responseB=jacResponse)
    print(comparison.scoreA, comparison.scoreB)
    # break
