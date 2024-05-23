import:py from jaclang.core.llms, Groq;

glob llm = Groq();


obj 'A work to be done in the future'
Task {
    has description: 'the content of the job to be done': str;
}

can 'give an estimated time for one to finish the task given' eta_llm(input: 'the task given': Task) -> 'estimated time in minutes': int by llm();

can 'give an estimated priority for the task' priority_llm(input: 'the task given': Task) -> 'priority score from 0 to 10, with 10 the most prioritized': int by llm();

obj 'A work to be done in the future'
TaskInfo :Task: {
    has time: 'number of minutes for one to finish the job': int;
    has priority: 'priority score from 0 to 10';
}

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
        eta = eta_llm(task);
        priority = priority_llm(task);
        task_info = TaskInfo(description = task_content, time = eta, priority = priority);
        print(task_info);
        tasks.append(task_info);
    }
    print(tasks);
}
