from testkit import AIEvaluator, RunnerEvaluator
from datasets import load_dataset
import json

# gpt4eval = AIEvaluator("What is the answer to 1+1")
#
# eval = gpt4eval.eval("1.99998", "1+1")
# print(eval.preferA())
# print(eval.scoreA)
# print(eval.scoreB)


ds = load_dataset("codeparrot/apps", split="test")
iter = ds.iter(batch_size=1)
for i in iter:
    sample = {}
    sample['question'] = i['question'][0]
    sample['solution'] = json.loads(i['solutions'][0])[0]
    sample['input_output'] = json.loads(i['input_output'][0])
    print(sample)
    break
