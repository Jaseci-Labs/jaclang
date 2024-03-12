# import:py from jaclang_edgedb.api, FastAPI; 
include:jac extra;
import:py from fastapi, HTTPException;


node Agents {
}

node Agent {
    has name: str;
}

edge HasAgents {}

edge HasAgent {}

walker TestAsync {
    async can walk with `<root> entry {
        print("HELLLO");
    }
}

walker CreateAgent {
    has name: str;
    has age: int = 20;

    can setup with `<root> entry {
        visit -:HasAgents:-> else {
            <root>+:HasAgents:+>Agents();
            visit -->;
        }
    }

    can create with Agents entry {
        print("here is ", <here>);
        <here>+:HasAgent:+>(agent := Agent(name=<self>.name));
        report agent;
    }
}


walker UpdateAgentNow {
    has name: str;

    obj Specs {
        static has method: str = "PUT", tags: list = ["Agents"]; 
    }

    can update with Agent entry {
        <here>.name = <self>.name;
        print("here is ", <here>);
        report <here>;
    }
}

walker DeleteAgent {
    can delete with Agent entry {
        # <here>.name = <self>.name;
        # print("here is ", <here>);
        <here>.destroy();
        report <here>;
    }
}

walker ListAgents {
    has limit: int = 1;
    has offset: int = 0;

    obj Specs {
        static has method: str = "GET", tags: list = ["Agents"];
    }

    can travel_root with `<root> entry {
        print("IP is: ", <self>.get_request().client.host);
        visit -:HasAgents:->;
    }
    
    can list with Agents exit {
        for i in -:HasAgent:-> {
            report i;
        }
    }
}


# with entry {
#     FastAPI.start(host="0.0.0.0", port=8000);
# }