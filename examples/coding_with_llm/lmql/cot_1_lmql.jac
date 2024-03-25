# """Q: It was Sept. 1st, 2021 a week ago. What is the date 10 days ago in MM/DD/YYYY?
# Answer Choices: (A) 08/29/2021 (B) 08/28/2021 (C) 08/29/1925 (D) 08/30/2021 (E) 05/25/2021 (F) 09/19/2021
# """

# # chain-of-thought instruction
# "A: Let's think step by step.\n"

# # free-form reasoning
# "[REASONING]\n"

# # constrain the final answer to robustly extract the result
# "Therefore, among A through F, the answer is[RESULT]" where \
#     RESULT in ["A", "B", "C", "D", "E", "F"]

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

can 'Provide the Answer for the Given Question (A-F)'
get_answer(question: 'Question' str, choices: 'Answer Choices': dict) -> 'Answer (A-F)' str by llm(reason=True);

with entry {
    question: str = "It was Sept. 1st, 2021 a week ago. What is the date 10 days ago in MM/DD/YYYY?";
    choices: dict = {
        "A": "08/29/2021",
        "B": "08/28/2021",
        "C": "08/29/1925",
        "D": "08/30/2021",
        "E": "05/25/2021",
        "F": "09/19/2021"
    };
    print(get_answer(question, choices));
}