# dimensions = ["Clarity", "Originality", "Evidence"]
# @function
# def essay_judge(s, essay):
#     s += "Please evaluate the following essay. " + essay
#     # Evaluate an essay from multiple dimensions in parallel
#     forks = s.fork(len(dimensions))
#     for f, dim in zip(forks, dimensions):
#         f += (
#            "Evaluate based on the following metric: " +
#            dim + ". End your judgement with the word 'END'")
#         f += "Judgment: " + f.gen("judgment", stop="END")
#     # Merge judgments
#     for f, dim in zip(forks, dimensions):
#         s += dim + ": " + f["judgment"]
#     # Generate a summary and give a score
#     s += "In summary," + s.gen("summary")
#     s += "I give the essay a letter grade of " +
#     s += s.gen("grade", choices=["A", "B", "C", "D"])
# ret = essay_judge.run(essay="A long essay ...")
# print(ret["grade"])

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