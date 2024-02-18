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
    has model_name: "gpt-3.5",
        temperature: 0.7,
        do_sample: true;
}

can 'get the best person to answer the question'
getExpert(question:'question' str)->' expert  ' str with llm;
can 'get the answer for the question from the expert(professional)'
getAnswerForQuestion(question:'question' str,expert:'expert' str)->'answer for the question' str with llm;

with entry{
    question = '''What are Large Language Models?'''
    expert=getExpert(question);
    print(expert);
    answer=getAnswerForQuestion(question,expert);
    print(answer);
}