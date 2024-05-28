import:py from jaclang.core.llms, Ollama;

glob llm = Ollama(model="phi3");


obj 'A work to be done in the future'
Task {
    has description: 'the content of the job to be done': str;
}


obj 'A work to be done in the future'
TaskFull {
    has description: 'the content of the job to be done': str;
    has time: 'number of minutes for one to finish the job': int;
    has priority: 'priority score from 0 to 10': int;
}

can 'give an estimated time for one to finish the task given and give an estimated priority for the task' taskfull_llm(input: 'the task given': Task) -> 'all information': TaskFull by llm();

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
        task = Task(description = task_content);
        task_info = taskfull_llm(task);
        print(task_info);
        tasks.append(task_info);
    }
    print(tasks);
}
