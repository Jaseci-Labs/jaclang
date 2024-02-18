model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

obj 'gradeEssay'
grader{
    has grade:'grade' list=['A', 'B', 'C', 'D'],
        criteria:'criteria to be considered.' list=['Clarity', 'Originality', 'Evidence'];
    
    can 'grade the given Essay for all the criteria' 
    gradeEssay(essay:'essay' str)-> 'grade of the essay for each criteria' dict with llm;
    
    can 'summary for why the grades are given for each criteria starts with 'In summary,'
    summarizeEssay(essae:'essay' str,grades :'grades ' dict)->'summary of why grades are given' str with llm;
}

with entry{
    essay = '''With a population of approximately 45 million Spaniards and 3.5 million immigrants,
               Spain is a country of contrasts where the richness of its culture blends it up with
               the variety of languages and dialects used. Being one of the largest economies worldwide,
               and the second largest country in Europe, Spain is a very appealing destination for tourists 
               as well as for immigrants from around the globe. Almost all Spaniards are used to speaking at 
               least two different languages, but protecting and preserving that right has not been 
               easy for them.Spaniards have had to struggle with war, ignorance, criticism and the governments, 
               in order to preserve and defend what identifies them, and deal with the consequences.'''
    judge=grader();
    output=judge.gradeEssay(essay);
    print(output);
    summary=judge.summarizeEssay(essay,output);
    print(summary);
}
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