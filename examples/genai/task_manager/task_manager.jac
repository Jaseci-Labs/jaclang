import:py from jaclang.core.llms, Ollama;

# glob llm = OpenAI(model_name="gpt-3.5-turbo");
glob llm = Ollama(host="http://52.23.242.52:11343");

obj 'A work to be done in the future'
Task {
    has description: 'Content of the Job to be done': str;
    has time: 'Estimated time in minutes for one to finish the job': int,
        priority: 'Estimated Priority for the Task (0-10)': int;
}

can task_llm(description: str) -> Task by llm(method="Reason");

with entry {
    task_contents = [
        "Have some sleep",
        "Enjoy a better weekend with my girlfriend",
        "Work on Jaseci Project",
        "Teach EECS 281 Students",
        "Enjoy family time with my parents"
    ];
    tasks = [];
    for task_content in task_contents {
        task_info = Task(description = task_content by llm(method="Reason"));
        print(task_info);
        tasks.append(task_info);
    }
    print(tasks);
}
