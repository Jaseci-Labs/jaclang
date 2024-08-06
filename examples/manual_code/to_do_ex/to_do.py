import datetime

# Enum for task status
from enum import Enum

class TaskStatus(Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"

# Dataclass style for a Task
class Task:
    def __init__(self, description, status=TaskStatus.PENDING):
        """
        Initialize a task.

        Arguments:
        description -- description of the task
        status -- status of the task (Pending, Completed)
        """
        self.description = description
        self.status = status
        self.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Dataclass style for the ToDoList
class ToDoList:
    def __init__(self):
        """
        Initialize the to-do list.
        """
        self.tasks = []

    def add_task(self, description):
        """
        Add a task to the to-do list.
        Arguments:
        description -- description of the task
        """
        self.tasks.append(Task(description))

    def view_tasks(self):
        """
        View all tasks in the to-do list.
        """
        for i, task in enumerate(self.tasks):
            print(f"{i+1}. {task.description} [{task.status.value}] (Created at: {task.created_at})")

    def mark_completed(self, index):
        """
        Mark a task as completed.
        Arguments:
        index -- index of the task to mark as completed
        """
        if index < 0 or index >= len(self.tasks):
            print("Invalid task number!")
            return
        self.tasks[index].status = TaskStatus.COMPLETED

# Function to display menu
def display_menu():
    """
    Display the menu options.
    """
    print("To-Do List Menu:")
    print("1. Add Task")
    print("2. View Tasks")
    print("3. Mark Task as Completed")
    print("4. Exit")

# Function to handle user input
def handle_input():
    """
    Handle user input for menu options.
    """
    to_do_list = ToDoList()
    while True:
        display_menu()
        choice = input("Enter your choice (1-4): ") or "4"
        if choice == "1":
            description = input("Enter task description: ") or ""
            to_do_list.add_task(description)
        elif choice == "2":
            to_do_list.view_tasks()
        elif choice == "3":
            index = int(input("Enter task number to mark as completed: ") or "-1") - 1
            to_do_list.mark_completed(index)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice! Please enter a number between 1 and 4.")

# Entry point of the app
if __name__ == "__main__":
    handle_input()

# # Unit Tests
# def test_add_task():
#     to_do_list = ToDoList()
#     to_do_list.add_task("Test Task")
#     assert len(to_do_list.tasks) == 1
#     assert to_do_list.tasks[0].description == "Test Task"

# def test_mark_completed():
#     to_do_list = ToDoList()
#     to_do_list.add_task("Test Task")
#     to_do_list.mark_completed(0)
#     assert to_do_list.tasks[0].status == TaskStatus.COMPLETED

# def test_invalid_task_number():
#     to_do_list = ToDoList()
#     to_do_list.add_task("Test Task")
#     to_do_list.mark_completed(1)
#     assert to_do_list.tasks[0].status == TaskStatus.PENDING

# # Running unit tests
# test_add_task()
# test_mark_completed()
# test_invalid_task_number()
# print("All tests passed.")
