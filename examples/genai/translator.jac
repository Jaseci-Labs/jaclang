import:py from model, OpenAIModel, ClaudeModel;

model llm:ClaudeModel {
    model_name="claude-3-sonnet-20240229";
}

# model llm:OpenAIModel {
#     model_name="gpt-4";
# 
 
 can 'Translate English Representation to the given language'
translate(input: 'English Representation': str, lang: 'Desired Language': str = "French")-> 'Translation': str by llm();

with entry {
    print(translate("I am a student", "French"));
    print(translate("I am a student", "Language used in Somalia"));
}