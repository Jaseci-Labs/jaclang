```jac
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
 ```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.

[Information]
Essay (str) (essay) =  'With a population of approximately 45 million Spaniards and 3.5 million immigrants, Spain is a country of contrasts where the richness of its culture blends it up with the variety of languages and dialects used. Being one of the largest economies worldwide, and the second largest country in Europe, Spain is a very appealing destination for tourists as well as for immigrants from around the globe. Almost all Spaniards are used to speaking at least two different languages, but protecting and preserving that right has not been easy for them.Spaniards have had to struggle with war, ignorance, criticism and the governments, in order to preserve and defend what identifies them, and deal with the consequences.'

[Inputs and Input Type Information]
criteria (str) (criteria) = 'Clarity'

[Output Type]
str

[Output Type Explanations]
Judgement (str)

[Action]
Evaluate the given essay based on the given criteria. Provide Detailed Judgement.

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result for Clarity
```yml
[Output] The essay is very clear. It provides precise facts and figures to deliver its points and uses simple and direct language. The flow of information is smooth and the ideas are logically connected. The sentences are well-structured and there is no ambiguity or confusion.
```
Result for Originality
```yml
[Output] The essay provides a generic overview of Spain, which contains commonly known facts. Despite presenting some unique aspects about the language scenario in the country, it lacks a unique perspective or innovative ideas. Therefore, based on the criteria of 'Originality', the essay can be judged as 'Moderately Original'.
```
Result for Evidence
```yml
[Output] The essay provides satisfactory evidence by presenting tangible facts and figures like population count, language fluency, and economic status. However, it lacks specific historical and contemporary examples to support claims about struggles and conflicts. Therefore, while it does present evidence, it could be improved by providing more detailed examples and citations.
```
---

```jac
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
judgements = essay.essay_judge_v2(criterias);
 ```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.

[Information]
Essay (str) (essay) =  'With a population of approximately 45 million Spaniards and 3.5 million immigrants, Spain is a country of contrasts where the richness of its culture blends it up with the variety of languages and dialects used. Being one of the largest economies worldwide, and the second largest country in Europe, Spain is a very appealing destination for tourists as well as for immigrants from around the globe. Almost all Spaniards are used to speaking at least two different languages, but protecting and preserving that right has not been easy for them.Spaniards have had to struggle with war, ignorance, criticism and the governments, in order to preserve and defend what identifies them, and deal with the consequences.'

[Inputs and Input Type Information]
Criterias (list[str]) (criterias) = ['Clarity', 'Originality', 'Evidence']

[Output Type]
dict [str, str]

[Output Type Explanations]
Judgements in Detail (dict[str, str])

[Action]
Evaluate the given essay based on the given criterias. Provide Detailed Judgement

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] {'Clarity': 'High - The essay is well-structured and presents the information clearly and concisely.', 'Originality': 'Medium - While the content is well-written, it mainly provides general information about Spain, which may not be considered original.', 'Evidence': 'High - The essay includes specific details such as population, language diversity, and historical struggles, which support its statements.'}
```
---
```jac
summary = essay.generate_summary(judgements);
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.

[Information]
Essay (str) (essay) =  'With a population of approximately 45 million Spaniards and 3.5 million immigrants, Spain is a country of contrasts where the richness of its culture blends it up with the variety of languages and dialects used. Being one of the largest economies worldwide, and the second largest country in Europe, Spain is a very appealing destination for tourists as well as for immigrants from around the globe. Almost all Spaniards are used to speaking at least two different languages, but protecting and preserving that right has not been easy for them.Spaniards have had to struggle with war, ignorance, criticism and the governments, in order to preserve and defend what identifies them, and deal with the consequences.'

[Inputs and Input Type Information]
Judgements (dict) (judgements) = {'Clarity': 'The essay is very clear. It provides precise facts and figures to deliver its points and uses simple and direct language. The flow of information is smooth and the ideas are logically connected. The sentences are well-structured and there is no ambiguity or confusion.', 'Originality': 'The essay provides a generic overview of Spain, which contains commonly known facts. Despite presenting some unique aspects about the language scenario in the country, it lacks a unique perspective or innovative ideas. Therefore, based on the criteria of 'Originality', the essay can be judged as 'Moderately Original'.', 'Evidence': 'The essay provides satisfactory evidence by presenting tangible facts and figures like population count, language fluency, and economic status. However, it lacks specific historical and contemporary examples to support claims about struggles and conflicts. Therefore, while it does present evidence, it could be improved by providing more detailed examples and citations.'}

[Output Type]
str

[Output Type Explanations]
Summary (str)

[Action]
Generate a summary

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] The essay about Spain is judged as clear and logically structured, with precise facts and figures. However, it lacks originality and could benefit from a unique perspective or innovative ideas. While it presents satisfactory evidence, it could be improved by providing more detailed examples and citations to support its claims.
```
---
```jac
grade = essay.give_grade(summary);
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.

[Information]
None

[Inputs and Input Type Information]
Summary (str) (summary) = 'The essay about Spain is judged as clear and logically structured, with precise facts and figures. However, it lacks originality and could benefit from a unique perspective or innovative ideas. While it presents satisfactory evidence, it could be improved by providing more detailed examples and citations to support its claims.'

[Output Type]
str

[Output Type Explanations]
Grade (str)

[Action]
Give essay a letter grade (A-D)

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] B
```