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

obj Essay {
    has essay: 'Essay' str;

    can 'Evaluate the given essay based on the given criteria. Provide Detailed Judgement.'
    essay_judge(criteria: 'Criteria' str) -> 'Judgement' str with llm;
    can 'Generate a summary'
    generate_summary(judgements: 'Judgements' dict) -> 'Summary' str with llm;
    can 'Give essay a letter grade (A-D)'
    give_grade(summary: 'Summary' str) -> 'Grade' str with llm(except=<self>.essay);

    can 'Evaluate the given essay based on the given criterias. Provide Detailed Judgement'
    essay_judge_v2(criterias: 'Criterias' list[str]) -> 'Judgements in Detail' dict[str, str] with llm;
}


with entry{
    essay = '''With a population of approximately 45 million Spaniards and 3.5 million immigrants,
               Spain is a country of contrasts where the richness of its culture blends it up with
               the variety of languages and dialects used. Being one of the largest economies worldwide,
               and the second largest country in Europe, Spain is a very appealing destination for tourists 
               as well as for immigrants from around the globe. Almost all Spaniards are used to speaking at 
               least two different languages, but protecting and preserving that right has not been 
               easy for them.Spaniards have had to struggle with war, ignorance, criticism and the governments, 
               in order to preserve and defend what identifies them, and deal with the consequences.''';
    essay = Essay(essay);

    criterias = ["Clarity", "Originality", "Evidence"];
    judgements = {};
    for criteria in criterias {
        judgement = essay.essay_judge(criteria);
        judgements[criteria] = judgement;
    }
    summary = essay.generate_summary(judgements);
    grade = essay.give_grade(summary);
}