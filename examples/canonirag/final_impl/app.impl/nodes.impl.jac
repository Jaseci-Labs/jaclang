:node:router:can:route {
    task:task_type = self.router_with_llm(query = here.query, todo_list = here.todo_list, user_data = here.user_data);
    if task == task_type.RAG_TYPE {
        visit [-->](`?RAG_chat);
    } elif task == task_type.TODO_TYPE {
        visit [-->](`?todo_chat);
    } elif task == task_type.QA_TYPE | task != None {
        visit [-->](`?user_qa_chat);
    }
}

:node:todo_chat:can:run_todo {
    print('routed --> TODO');

    response = self.chat_llm(
            todo_list=here.todo_list,
            user_data=here.user_data,
            query=here.query,
            chat_history=here.messages
        );
    gui.display_response(response);
    here.messages.append({"role": "assistant", "content": response});
    save_data(messages = here.messages) spawn here;
}

:node:user_qa_chat:can:run_user_qa {
    print('routed --> USER_QA');

    response = self.chat_llm(
            user_data=here.user_data,
            query=here.query,
            chat_history=here.messages
        );
    gui.display_response(response);
    here.messages.append({"role": "assistant", "content": response});
    save_data(messages = here.messages) spawn here;
}

:node:RAG_chat:can:run_RAG {
    print('routed --> RAG');
    
    response = self.chat_llm(
            todo_list=here.todo_list,
            user_data=here.user_data,
            query=here.query,
            chat_history=here.messages,
            retrived_context=RagEngine.get_from_chroma(query=here.query)
        );
    gui.display_response(response);
    here.messages.append({"role": "assistant", "content": response});
    save_data(messages = here.messages) spawn here;
}