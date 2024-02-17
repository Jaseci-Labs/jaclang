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

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

obj 'Question Answering'
QA  {
    has qa_list :'QA List ': list[dict] =[
        {
            "question": "What is the elevation range for the area that the eastern '
                         'sector of the Colorado orogeny extends into?' 
        },
        {
            'Thought':'I need to search Colorado orogeny, find the area that the eastern'
                     'sector of the Colorado ...\n"
        },
        {
           'Action':'Search \'Colorado orogeny\'\n'
        },
        {
            'Observation':'The Colorado orogeny was an episode of mountain building (an orogeny) ...\n'
        },
        {
            'Thought': 'It does not mention the eastern sector. So I need to look up eastern sector.\n'
        },
        {
            'Thought':' High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.'
        },
        {
            "Action": "Finish \'1,800 to 7,000 ft\'"
        },
    ]

    can ' generate appropriate new dictionary for answering (it can be Thought / Action / Observation) '
     generte_new_ditionary ->'Answer' dict with llm{}

   

   can recurse{
        if (qa_list[-1].keys())[0]=='Action' and 'finish' in (qa_list[-1].values())[0] : 
            return (qa_list[-1].values())[0]
        else:
            if wiki needed:
                search_wiki();


            else:
                new_dict=generte_new_ditionary();
                qa_list.append(new_dict)
                recurse();
   }

   can 'Question_asnwering'
   Question_asnwering(question: str){
       qa_list.append({'question':question});
       generte_new_ditionary();
       recurse();
   }

}