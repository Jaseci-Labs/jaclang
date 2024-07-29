import:py streamlit as st;
import:py from PIL, Image;

can page_build {
    st.set_page_config(
                    page_title="JacCare Health Assistant",
                    page_icon=":robot:",
                    layout="wide");

    st.image(Image.open("images/JacCare LOGO.png"));
    st.title("Jac${Care}$");
}

can chat_interface(query_walker:walker){
    for message in query_walker.messages {
        with st.chat_message(message["role"]) {
            st.markdown(message["content"]);
        }
    }

    if input := st.chat_input("What is up?") {
        query_walker.query = input;
        query_walker.messages.append({  "role": "user", 
                                        "content": query_walker.query});
        with st.chat_message("user"){
            st.markdown(query_walker.query);
        }
    }
}

can display_response(response:str){
    with st.chat_message("assistant"){
        stream = st.write(response);
    }
}