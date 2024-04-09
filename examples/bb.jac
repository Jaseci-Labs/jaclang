"""A Number Guessing Game"""

# glob x :int =9  ,  y:str='shjh';

# glob x:int,y:str;

walker Creator {
    can func2 with `root entry ;
}

node node_1 {
    has val: int;    
    can func_1 with Creator entry ;
}

:node:node_1:can:func_1() {
    print("visiting ", self) ;    
    visit [-->];
}

:walker:Creator:can:func2() {
    end=here;    
    for i=0 to i<5 by i+=1  {
        end ++> (end := node_1(val=i + 1)) ;
    }
    
    visit [-->];
}

with entry {
    root spawn :> Creator ;    
    root spawn |> Creator ;
}

# import:py random;

# walker GuessGame {
#     has correct_number: int = (1, 100) |> random.randint;

#     can start_game with `root entry;
#     can process_guess(guess: int);
# }

# node turn {
#     can check with GuessGame entry;
# }

# :node:turn:can:check {
#     guess = "Guess a number between 1 and 100: " |> input;
#     if |> guess.isdigit {
#         guess |> int |> here.process_guess;
#     } else {
#         "That's not a valid number! Try again." |> print;
#     }
#     # visit [-->];
# }

# :walker:GuessGame:can:start_game {
#     end = here;
#     # for i=0 to i<10 by i+=1  {
#     #     end ++> (end := turn());
#     # }
# }



# with entry {
#     :> GuessGame spawn root;
#     visit [-->];
# }
