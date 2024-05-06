import:py from jaclang.core.llms, Anthropic;

glob llm = Anthropic(model_name="claude-3-sonnet-20240229");

node user_session {
    has id:str;
    has chat_history:list=[];
    has user_data:dict;

}

node router {
    can 'route the query to the appropriate task type'
    classify(query:str) -> task;

    can _route with query entry {
        task_type:task = classify(query);
    }
}

node RAG;
node todo;
node user_qa;

walker query;

enum 'The type of task required to run'
task {
    RAG : 'Use Retrivable information' = "RAG",
    PERSONAL : 'Use given user information' = "user_qa",
    TODO : 'Use the todo list of the user' = "todo"
}

