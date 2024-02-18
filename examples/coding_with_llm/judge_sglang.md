```jac
 output=judge.gradeEssay(essay)
 ```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
grade (list) (grade)=['A', 'B', 'C', 'D']
criteria to be considered. (list) (criteria)=['Clarity', 'Originality', 'Evidence']

[Inputs and Input Type Information]
essay (str) essay ='''With a population of approximately 45 million Spaniards and 3.5 million immigrants,Spain is a country of contrasts where the richness of its culture blends it up withthe variety of languages and dialects used. Being one of the largest economies worldwide,and the second largest country in Europe, Spain is a very appealing destination for tourists as well as for immigrants from around the globe. Almost all Spaniards are used to speaking at least two different languages, but protecting and preserving that right has not been easy for them.Spaniards have had to struggle with war, ignorance, criticism and the governments, in order to preserve and defend what identifies them, and deal with the consequences.'''
   

[Output Type]
dict

[Output Type Explanations]
grade of the essay for each criteria (dict) 

[Action]
grade the given Essay for all the criteria.

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] {'Clarity': 'B', 'Originality': 'A', 'Evidence': 'C'}
```

```jac
summary=judge.summarizeEssay(essay,output)
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
grade (list) (grade)=['A', 'B', 'C', 'D']
criteria to be considered. (list) (criteria)=['Clarity', 'Originality', 'Evidence']

[Inputs and Input Type Information]
essay (str) essay ='''With a population of approximately 45 million Spaniards and 3.5 million immigrants,Spain is a country of contrasts where the richness of its culture blends it up withthe variety of languages and dialects used. Being one of the largest economies worldwide,and the second largest country in Europe, Spain is a very appealing destination for tourists as well as for immigrants from around the globe. Almost all Spaniards are used to speaking at least two different languages, but protecting and preserving that right has not been easy for them.Spaniards have had to struggle with war, ignorance, criticism and the governments, in order to preserve and defend what identifies them, and deal with the consequences.'''
grades (list) (grades)={'Clarity': 'B', 'Originality': 'A', 'Evidence': 'C'}

[Output Type]
str

[Output Type Explanations]
summary of why grades are given (str) 

[Action]
summary for why the grades are given for each criteria starts with 'In summary,'

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>


```
Result

```yml
[Output] In summary, the grade for Clarity is 'B' because the essay effectively presents ideas but could be clearer in some areas. In summary, the grade for Originality is 'A' because the essay demonstrates a unique and creative perspective. In summary, the grade for Evidence is 'C' because the essay lacks strong supporting evidence.
```