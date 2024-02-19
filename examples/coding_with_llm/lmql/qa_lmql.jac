# import wikipedia_utils
# sample(no_repeat_ngram_size=3)
# "What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?"
# "Tho 1: I need to search Colorado orogeny, find the area that the eastern sector of the Colorado ...\n"
# "Act 2: Search 'Colorado orogeny'\n"
# "Obs 2: The Colorado orogeny was an episode of mountain building (an orogeny) ...\n"
# "Tho 3: It does not mention the eastern sector. So I need to look up eastern sector.\n"
# ...
# "Tho 4: High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft."
# "Act 5: Finish '1,800 to 7,000 ft'"
# "Where is Apple Computers headquartered?\n"
# for i in range(1024):
# "[MODE] {i}:"
# if MODE == "Tho":
# "[THOUGHT] "
# elif MODE == "Act":
# " [ACTION] '[SUBJECT]\n"
# if ACTION == "Search":
# result = wikipedia_utils.search(SUBJECT[:-1]) # cutting of the consumed '
# "Obs {i}: {result}\n"
# else:
# break # action must be FINISH
# from "gpt2-xl"
# where
# MODE in ["Tho", "Act"] and stops_at(THOUGHT, "\n") and
# ACTION in ["Search", "Finish"] and len(words(THOUGHT)) > 2 and
# stops_at(SUBJECT, "'") and not "Tho" in THOUGHT

import:py wikipedia;

model llm:openai {
    has model_name: "gpt-4",
        temperature: 1.0,
        do_sample: true;
}

obj 'Question Answering'
QA {
    has qa_example: 'QA example with Thoughts and Actions': list[dict] = [
        {
            "Question": "What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?",
            "Thoughts and Observations": [
                {
                    "Thought": "I need to search Colorado orogeny, find the area that the eastern sector of the Colorado ...",
                    "Action": "Search 'Colorado orogeny'",
                    "Observation": "The Colorado orogeny was an episode of mountain building (an orogeny) ..."
                },
                {
                    "Thought": "It does not mention the eastern sector. So I need to look up eastern sector.",
                    "Action": "Search 'eastern sector of the Colorado orogeny'",
                    "Observation": "The eastern sector of the Colorado orogeny extends into the High Plains."
                },
                {
                    "Thought": "High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.",
                    "Action": "Finish '1,800 to 7,000 ft'"
                }
            ]
        }
    ];

    can 'Get next Thought and Action'
    get_throught_and_actions(question: 'Question' str, prev_info: 'Previous Thoughts, Actions, and Observations' list[dict] = []) -> 'Next Thought and Action' dict with llm;

    can get_answer(question: 'Question' str) -> str {
        got_answer = False;
        prev_info = [];
        while not got_answer and len(prev_info) < 100 {
            next_info = get_throught_and_actions(question, prev_info);
            if next_info["Action"].startswith("Search") {
                obs = wikipedia.summary(next_info["Action"].replace("Search ", "").replace("'", ""));
                next_info["Observation"] = obs;
            } elif next_info["Action"].startswith("Finish") {
                got_answer = True;
                return next_info["Action"].replace("Finish ", "").replace("'", "");
            }
            prev_info.append(next_info);
        }
    }
}

with entry {
    qa = QA();
    print(qa.get_answer("Where is Apple Computers headquartered?"));
}