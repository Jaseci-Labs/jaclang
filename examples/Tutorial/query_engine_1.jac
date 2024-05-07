import:py from jaclang.core.llms, Anthropic;

glob llm = Anthropic(model_name="claude-3-sonnet-20240229");

enum 'The type of task required to run'
task_type {
    RAG_type : 'Need to use Retrivable information in specific finacial articles' = "RAG",
    PERSONAL_type : 'Need to use given user information' = "user_qa",
    TODO_type : 'Need to use the todo list of the user' = "todo"
}

glob router_examples: 'Examples of routing of a query': dict[str, task_type] = {
    'How to become a millionier': task_type.RAG_type,
    'What is my savings balance?': task_type.PERSONAL_type
};

node user_session {
    has id:str;
    has chat_history:list=[];
    has user_data:dict={};
    has todo_list:list=[];

}

node router {
    can 'route the query to the appropriate task type'
    classify(query:str) -> task_type
    by llm(reason= True, temperature=0.0, incl_info=(router_examples));
}

edge q_eng {
    has edge_type:task_type = None;
}

walker query{
    has query:str;
    has user_session_id:str='';
    has session_chat_history:list=[];
    has user_data:dict={};
    has todo_list:list=[];

    can init_query_engine with user_session entry {
        self.user_session_id = here.id;
        self.user_data = here.user_data;
        self.todo_list = here.todo_list;
        self.session_chat_history = here.chat_history;

        end = here;
        end ++> (end := router());
        end +:q_eng:edge_type=task_type.RAG_type:+> RAG();
        end +:q_eng:edge_type=task_type.TODO_type:+> todo();
        end +:q_eng:edge_type=task_type.PERSONAL_type:+> user_qa();

        visit [-->];
    }

    can route with router entry {
        task:task_type = here.classify(query = self.query);
        if task == task_type.RAG_type {
            visit [-:q_eng:edge_type==task_type.RAG_type:->];
        } elif task == task_type.PERSONAL_type {
            visit [-:q_eng:edge_type==task_type.PERSONAL_type:->];
        } elif task == task_type.TODO_type {
            visit [-:q_eng:edge_type==task_type.TODO_type:->];
        }
    }
}

node RAG {
    can run_RAG with query entry {
        print('routed --> RAG');
    }
}

node todo {
    can run_todo with query entry {
        print('routed --> TODO');
    }
}

node user_qa {
    can run_user_qa with query entry {
        print('routed --> USER_QA');
    }
}

walker app{
    can run_app with `root entry{
        root ++> user_session( id="1234",
                                user_data={ "name":"John Doe",
                                            "salary_in_usd":2000,
                                            "debt_in_usd":20000,
                                            "savings_in_usd":15000
                                            },
                                todo_list=[ "Pay bills", "buy car", "buy house"]
                                );
        visit [-->];
    }

    can run_query with user_session entry {
        here spawn query(query=input('Ask a question : '));
    }
}

with entry {
    app() spawn root;
}

