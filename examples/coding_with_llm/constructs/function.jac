include:plugin openai;

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

can 'Summarize the Accomplishments'
summarize (a: 'Accomplishments' list[str]) -> 'Summary of the Accomplishments' str with llm;

can 'Translate the given text to Spanish'
translate (text: str) -> 'Translated Text' str with llm;

with entry{
    summary = summarize(a=["Albert Einstein won a nobel prize", "Discovered the Theory of Relativity"]);
    spanish_summary = translate(summary);
    print(f"Summary of the Accomplishments: {summary}\n Spanish Translation: {spanish_summary}");
}