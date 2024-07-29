:walker:chat:can:create_session {

        # Telescope into the nodes connected to the user node without walking.
        data_node = [-->](`?data)[0]; # Getting the data node filtered. can use [0] as having only one such node.
        todo_node = [-->](`?todo)[0]; # Getting the todo node filtered. can use [0] as having only one such node.
        new_session_id = str(random.randint(1000,9999));

        # Creating a new session node with the user data and todo list and connect it to the user.
        n = here ++> session(   session_id = new_session_id,
                            user_data = data_node.user_data,
                            todo_list = todo_node.todo_list
                        );
        visit n;
    }

:walker:chat:can:chat_session {
    # print(here.user_data);
    # print(here.todo_list);
    query() spawn here;
}

:walker:create_graph:can:generate_graph {
    end = here; # Assign the current root node (here) to end
    end ++> (end := user()); # Create a user node and connect it to the end node. Assign the new user node to the end.
    end ++> data(user_data = self.user_data); # Create a data node with the user data and connect it to the end node.
    end ++> todo(todo_list = self.todo_list); # Create a todo node with the todo list and connect it to the end node.
    chat() spawn [-->](`?user)[0]; # Spawn the chat walker with the user node.
}

:walker:query:can:init_query_engine {
    self.user_data:dict = here.user_data;
    self.todo_list:list = here.todo_list;
    self.messages:list = here.messages;

    if [here -->] == [] {
        end = here;
        end ++> (end := router());
        end ++> RAG_chat();
        end ++> todo_chat();
        end ++> user_qa_chat();
    }

    # gui.display_chat(self.messages);
    gui.chat_interface(query_walker=self);
    
    visit [-->];
}