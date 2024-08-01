import:py datetime;
import:py from enum { Enum }
import:py from random { randint }

enum TaskStatus {
    PENDING = "Pending",
    COMPLETED = "Completed"
}

"""
Initialize a task.
description -- description of the task
status -- status of the task (Pending, Completed)
"""
obj Task {
    has description: str;
    has status: TaskStatus = TaskStatus.PENDING;
    has created_at: datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S");
}

"""Initialize the to-do list."""
obj ToDoList {
    has tasks: list = [];

    can add_task(description: str) {
        self.tasks.append(Task(description));
    }

    can view_tasks() {
        if self.tasks {
            for (i, task) in enumerate(self.tasks) {
                print(
                    f"{(i + 1)}{". "}{task.description}{" ["}{task.status.value}{"] (Created at: "}{task.created_at}{")"}"
                );
            }
        } else {
            print("No tasks");
        }
    }

    can mark_completed(index: int) {
        if index < 0 or index >= len(self.tasks) {
            print("Invalid task number!");
        }
        self.tasks[index].status = TaskStatus.COMPLETED;
    }
}

can display_menu() {
    print("To-Do List Menu:");
    print("1. Add Task");
    print("2. View Tasks");
    print("3. Mark Task as Completed");
    print("4. Exit");
}

can handle_input() {
    to_do_list = ToDoList();

    while True {
        display_menu();
        choice = input("Enter your choice (1-4): ") or "4";
        if choice == "1" {
            description = input("Enter task description: ") or "";
            to_do_list.add_task(description);
        } elif choice == "2" {
            to_do_list.view_tasks();
        } elif choice == "3" {
            index = (int(
                input("Enter task number to mark as completed: ")
                    or "-1"
            ) - 1);
            to_do_list.mark_completed(index);
        } elif choice == "4" {
            print("Exiting...");
            break;
        } else {
            print(
                "Invalid choice! Please enter a number between 1 and 4."
            );
        }
    }
}
# can test_add_task() {
#     to_do_list = ToDoList();
#     to_do_list.add_task("Test Task");
#     assert len(to_do_list.tasks) == 1;
#     assert to_do_list.tasks[0].description == "Test Task";
# }
# can test_mark_completed() {
#     to_do_list = ToDoList();
#     to_do_list.add_task("Test Task");
#     to_do_list.mark_completed(0);
#     assert to_do_list.tasks[0].status == TaskStatus.COMPLETED;
# }
# can test_invalid_task_number() {
#     to_do_list = ToDoList();
#     to_do_list.add_task("Test Task");
#     to_do_list.mark_completed(1);
#     assert to_do_list.tasks[0].status == TaskStatus.PENDING;
# }

with entry {
    handle_input();
}
