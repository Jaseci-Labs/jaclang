import:py json;
import:py random;
import:py from mtllm.llms, OpenAI;
import:jac gui;
import:jac from rag, rag_engine;

glob llm1 = OpenAI(model_name='gpt-3.5-turbo');
glob llm2 = OpenAI(model_name='gpt-4');

glob RagEngine:rag_engine = rag_engine();

enum PR_states {
    init_PR = 'initial run',
    chat_create = 'create chat graph',
    chat = 'chat with user'
}

glob state = PR_states.init_PR;

'''
User node has user_name attribute.
'''
node user{
    has user_name:string="user";
}

'''
Chat session of a user. This node contains the session_id, user_data and todo_list.
This should also include the chat history. Can have multiple chat sessions.
'''
node session{
    has session_id : string = 100;
    has user_data : dict = {}; # User data such as habits, heart rate etc.
    has todo_list : list = []; # List of things to do by the user.
    has messages : list = []; # Chat history of the user.
}

'''
Consists of user data such as age, pressure, married status.
'''
node data{
    has user_data:dict = {
                "age" : 0,
                "Pressure" : (0,0),
                "Married" : False
                };
}

'''
List of things to do by the user.
'''
node todo{
    has todo_list:list = [];
}


'''
This is the chat walker which will be used to chat with the user.
The create_session ability:
    - gather the user data and todo list from connected nodes using filters.
    - Creates a new session with the user data and todo list.
    - Spawns the chat session with the session id.
'''
walker chat{
    can create_session with user entry;
}

'''
This is where we create the graph.
'''
walker create_graph{
    has user_data:dict = {};
    has todo_list:list = [];

    can generate_graph with `root entry;
}

'''
This is the query walker which will be used to query a user input and generate a response.
The init_query_engine ability:
    - Gathers the user data and todo list from the user node.
    - Asks the user for the routing method.
    - Creates a router node and connects it to the RAG_chat, todo_chat and user_qa_chat nodes.
    - Visits the router node.
'''
walker query{
    has query:str = '';
    has user_session_id:str='';
    has session_chat_history:list=[];
    has user_data: 'data about the health status of the user' :dict={};
    has todo_list: 'The tasks to be done by the user in the future.' :list=[];
    has messages:list = [];

    can init_query_engine with session entry;
}

enum task_type {
    RAG_TYPE : 'Need to use Retrivable information in specific medical articles' = "RAG",
    QA_TYPE : 'Need to use given user information' = "user_qa",
    TODO_TYPE : 'Need to use the todo list of the user' = "todo"
}

glob router_examples: 'Examples of routing of a query': dict[str, task_type] = {
    'When is my next check up?': task_type.TODO_TYPE,
    'How healthy am I?': task_type.QA_TYPE,
    'What are the symptoms of low blood pressure?': task_type.RAG_TYPE
};

'''
This is the router node which will be used to route the user query to the appropriate chat node.
'''
node router {
    can route with query entry;
    can 'route the query to the appropriate task type'
    router_with_llm(query:'Query from the user to be routed.':str,
                    todo_list:'The tasks to be done by the user in the future.':list,
                    user_data:'data about the health status of the user.':dict) -> task_type
                                        by llm2(method="Reason", temperature=0.0, incl_info=(router_examples));
}

'''
This is the RAG chat node which will be used to chat with the user using Retrival Augmented Generation.
TODO:Not yet implemented.
'''
node RAG_chat {
    can run_RAG with query entry;
    can 'You are a warmly Health Assistant named JacCare. Give a response based on the query using todo list. and user data'
    chat_llm(todo_list:'The tasks to be done by the user in the future.':list,
             user_data:'data about the health status of the user.':dict,
             query:'Question from the user to be answered.':str,
             retrived_context : 'Retrived information from expert articles':list,
             chat_history:'Previous Conversation with the user':list) -> 'response':str by llm1(temperature =0.5);
}

'''
This is the TODO chat node which will be used to chat with the user using the todo list and user data.
'''
node todo_chat {
    can run_todo with query entry;
    can 'You are a warmly Health Assistant named JacCare. Give a response based on the query using todo list. and user data'
    chat_llm(todo_list:'The tasks to be done by the user in the future.':list,
             user_data:'data about the health status of the user.':dict,
             query:'Question from the user to be answered.':str,
             chat_history:'Previous Conversation with the user':list) -> 'response':str by llm1(temperature =0.5);
}

'''
This is the user QA chat node which will be used to chat with the user using the user data.
TODO:Not yet implemented.
'''
node user_qa_chat {
    can run_user_qa with query entry;
    can 'You are a warmly Health Assistant named JacCare. Give a response based on the query, using user data'
    chat_llm(user_data:'data about the health status of the user.':dict,
             query:'Question form the user.':str,
             chat_history:'Previous Conversation with the user':list) -> 'response':str by llm1(temperature =0.5);
}

walker save_data{
    has messages:list = [];
    can go_to_router with todo_chat | user_qa_chat | RAG_chat entry {
        visit [<--];
    }

    can go_to_session with router entry {
        visit [<--];
    }
    can save_data with session entry {
        here.messages = self.messages;
        disengage;
    }
}

can main {
    :g: state;
    :g: RagEngine;

    gui.page_build();

    if state == PR_states.init_PR {
        # Import the data from JSON file
        with open('user_info.json', 'r') as f{
            imported_data = json.load(f);
        }

        create_graph(   user_data = imported_data['user_data'],
                        todo_list = imported_data['todo_list']) spawn root;
    print('Graph created');
    state = PR_states.chat_create;
    query() spawn [[root -->](`?user)[0] -->](`?session)[0];
    } elif state == PR_states.chat_create {
        query() spawn [[root -->](`?user)[0] -->](`?session)[0];
        print('Chatting with user');
    } else {
        print('Invalid state');
    }

}

with entry {
    if __name__ == "__main__"{
        main();
    }
    
}