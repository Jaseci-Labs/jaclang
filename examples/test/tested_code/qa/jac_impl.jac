import:py from jaclang.core.llms, Ollama;
glob llm = Ollama(host="http://52.23.242.52:11343");
can answerquestion(question: str) -> 'answer': str by llm();

with entry{
    question = input();
    answer = answerquestion(question);
    print(answer);
}
