include:py typing_extensions;
import:py from typing, Annotated, Optional;
import:py pydantic;
import:py from fastapi, File, Form, UploadFile, Query, Path, Header, Security;
import:py from jaclang_edgedb.utils, api_key_auth;



walker UploadImage {
    has age: Annotated[int, Form(gt=4, title="GREAT", description="The age of the person")];
    has file: Annotated[list[bytes], File()] = None;
    has name: Annotated[Optional[str], Form(max_length=20, title="This is cool")] = None;
    # has id: Annotated[str, Path(title="ID of something")];
    
    
    # has smth: Annotated[str, StringConstraints(max_length=20)] = "SUP";

    can walk with `<root> entry {
        # print("files uploaded: ", len(<s>.file));
        report f"NAME is {<s>.name}";
        report f"AGE is {<s>.age}";
    }

    obj Specs {
        static has method: str = "POST", path: str = "/{id}";
    }
}

walker TestQuery {
    has name: Annotated[str | None, Query(title="Name of the person")] = 20;
    has age: Annotated[int | None, Query(gt=4, title="The age of the person")] = None;

    can walk with `<root> entry {
        report f"NAME is {<s>.name}";
        report f"AGE is {<s>.age}";
    }

    obj Specs {
        static has method: str = "GET";
    }
}

walker TestPath {
    has name: Annotated[str | None, Query(title="Name of the person")] = 20;
    has age: Annotated[int | None, Query(gt=4, title="The age of the person")] = None;
    

    can walk with `<root> entry {
        report f"NAME is {<s>.name}";
        report f"AGE is {<s>.age}";
    }

    obj Specs {
        static has method: str = "GET";
    }
}


walker TestHeaderParams {
    has secret_key: Annotated[str, Security(api_key_auth(valid_keys=["yo"]))];
    has user_agent: Annotated[str | None, Header()] = None;
    

    can walk with `<root> entry {
        report f"User-Agent is {<s>.user_agent}";
        report f"Secret-Key is {<s>.secret_key}";
    }
}


walker Guarded {
    has api_key: str;
    

    can walk with `<root> entry {
        report f"Key is {<s>.api_key}";
    }
}