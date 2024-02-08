'''Model'''
model llm {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}
'''Function'''
can 'Summarize the Accomplishments'
summarize ('Accomplishments' a: List[String]) -> 'Summary of the Accomplishments' summary: String Using llm{

}

with entry{
    summarize(a=["Won Nobel Prize", "Discovered the Theory of Relativity"]);
}