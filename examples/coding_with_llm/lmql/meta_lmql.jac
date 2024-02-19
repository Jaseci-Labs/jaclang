# # use beam search to explore different potential 'expert' values
# beam(n=2)
#     "Q: What are Large Language Models?\n\n"

#     # prompt for an 'expert'
#     "A good person to answer this question would be[EXPERT]\n\n" where \
#         STOPS_AT(EXPERT, ".") and STOPS_AT(EXPERT, "\n")
#     expert_name = EXPERT.rstrip(".\n")

#     # use 'expert' to answer the question
#     "For instance,{expert_name} would answer[ANSWER]" where STOPS_AT(ANSWER, ".")
# from
#     "openai/text-davinci-003"

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

can 'Finds the best professional to answer the given question'
get_expert(question: 'Question' str)->' Expert Profession' str with llm(ends_at="\n");
can "Get the answer for the question from expert's perspective"
get_answer(question:'Question' str, expert: 'Expert' str)-> "Expert's Answer" str with llm(ends_at=".");

with entry{
    question = "What are Large Language Models?";
    expert = get_expert(question);
    answer = get_answer(question, expert);
    print(f"For instance, {expert} would answer {answer} for the question {question}");
}