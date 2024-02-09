include:plugin openai;

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

can 'Summarize the Accomplishments'
summarize ('Accomplishments' a:list[str]) -> 'Summary of the Accomplishments' summary:str with llm {
    return summary;
}

"""if the codeblock of the function is left empty, the function will automatically return the output
Reason behind is unlike tradional programming wher the return type is only specified but in this case the return is a type and a value that is coming through the llm
so the function will automatically return the output"""
can 'Translate the given text to Spanish'
translate (text:str) -> 'Translated Text' translation:str with llm;

with entry{
    summary = summarize(a=["Albert Einstein won a nobel prize", "Discovered the Theory of Relativity"]);
    spanish_summary = translate(summary);
    print(f"Summary of the Accomplishments: {summary}\n Spanish Translation: {spanish_summary}");
}