
"""This is the Data Spatial Implementation of the RPG Game"""

# This game is built using the pygame module which is imported here

import:py pygame;
import:py sys;
import:py random;
import:py time;
import:py openai;
import:py from openai, ChatCompletion;
import:py re;
import:py ast;

# Importing Jac codebase
include:jac sprites;
include:jac config;
include:jac map;
include:jac main;


import:py os;
import:py dspy;

import:py from pydantic, BaseModel, Field;


glob context_info:str =  "The game is a simple RPG game where the player is the character controlled by the person playing the game."
                "The game has multiple levels and each level is different and incrementally challenging than the previous levels."
                "The player has to complete each level by reaching the end of the level without getting caught by the enemies."
                "The enemies are represented by the letter 'E' in the map and the player is represented by the letter 'P'."
                "The player can move in all four directions (up, down, left, right) and the enemies move randomly in the map."
                "The player has to avoid the enemies and reach the end of the level to complete the level."
                "The player can collect power-ups and other items in the map to help them complete the level faster."
                "The game is designed to be simple and fun to play, with each level getting more challenging as the player progresses through the game."
                "Each newly generated map should be different from the previous one.";

class Input:BaseModel: {
    has map_directory:dict[str,Map] = Field(description = "Contains all the levels and their configurations of a game where"
                                                          "the player is the character controlled by the person playing the game");
    has context:str = Field(description = "Context for the model");
}

class Output:BaseModel: {
    has map: list[str] = Field(description= "A list of strings representing the map of the level. Each string corresponds to the row of the map.");

}

"""Return the map of the next level which is different and incrementally challenging than previous levels."""
class MapGenTask:dspy.Signature:{

    has input:Input = dspy.InputField();
    has output:Output = dspy.OutputField();

}

'''The walker that initiates the game and runs an instance of the game'''
walker game{

    has g:Game = None,
        current_level:int = 1,
        fwd_dir:bool = True,
        map_directory:dict={};

    can start_game with `root entry;
    can generate_level;
    can generate_level_dspy;
}

edge play{

    has level_id:str = '1_1000';
}

'''Start screen node which operate as the virtual root node'''
node start_screen {

    has game_started:bool = False;

    can intro_screen with game entry;
    can exit_game with game exit;

}

'''Level node which (should) have unique (ai generated) attributes'''
node level{
    has game_level:int = 1,
        level_id:str = '1_1000',
        played:bool = False,
        level_config:Map = Map(),
        level_time:float=500000;

    can run_game with game entry;
    can exit_game with game exit;
}

'''Run the game'''
with entry {
    llm = model();
    gpt4:Any = dspy.OpenAI(model='gpt-4', max_tokens=300);
    dspy.configure(lm=gpt4);
    game() spawn root;
}

#=Walker=&=Node=Abilities=======================================

:walker:game:can:generate_level_dspy() {
    gen_map = dspy.TypedPredictor(MapGenTask);
    new_map = gen_map(input=Input(map_directory=self.map_directory, context=context_info));
    return new_map.output.map;
}

:walker:game:can:start_game {
    self.g = Game();
    here ++> start_screen();
    visit [-->];
}

:walker:game:can:generate_level() {

    if self.map_directory {
        new_map = self.generate_level_dspy();
        for row in new_map {print(row, '\n');}
        self.map_directory[str(self.current_level)] = Map(map=new_map);
    } else {
        self.map_directory[str(self.current_level)] = Map();
    }
}

:node:level:can:run_game {
    # print("Walker Entry ->", self.level_id);

    if self.played == False {
        if here.current_level != self.game_level {
            here.current_level = self.game_level;
        }
        if str(self.game_level) not in here.map_directory.keys(){
            here.generate_level();
        }

        here.g.GameMap.map = here.map_directory[str(self.game_level)].map;
        here.g.new();
        print(":-: Playing Level :", self.game_level, "| Level ID :",  self.level_id, "| Played :", str(self.played));
        start_time = time.time();
        here.g.main();
        end_time = time.time();
        if here.g.won == True{
            self.level_time = end_time - start_time;
            here.map_directory[str(self.game_level)].time_to_win_level = self.level_time;
            # print('Time:', self.level_time);
            here.g.game_won();
            self.played = True;
            here.g.won = False;
            here.fwd_dir =True;
            new_ID = str(self.game_level+1) + "_" + str(random.randint(1000, 9000));
            self +:play:level_id=new_ID:+> level(game_level = self.game_level+1, level_id = new_ID);
            visit [-:play:level_id==new_ID:->];
        } else {
            here.g.game_over();
            self.played = True;
            here.g.won = False;
            here.fwd_dir = False;
            visit [<-:play:-];
        }
    } elif here.fwd_dir == False{
        new_ID = str(self.game_level+1) + "_" + str(random.randint(1000, 9000));
        print(":-: Visiting Level :", self.game_level, "| Level ID :",  self.level_id, "| Played :", str(self.played), '| Created Level ID :', new_ID);
        here.fwd_dir = True;
        self +:play:level_id=new_ID:+> level(game_level = self.game_level+1, level_id = new_ID);
        visit [-:play:level_id==new_ID:->];
    } else {
        print(":-: Visiting Level :", self.game_level, "| Level ID :",  self.level_id, "| Played :", str(self.played));
        visit [<--];
    }
}

:node:level:can:exit_game {
    if here.g.running == False {
        pygame.quit();
        sys.exit();
        disengage;
    }
}

:node:start_screen:can:intro_screen {
    # print("Walker Entry -> Intro Screen");
    if self.game_started == False {
        self.game_started = True;
        here.g.intro_screen();
        new_ID = str(1) + "_" + str(random.randint(1000, 9000));
        self +:play:level_id=new_ID:+> level(game_level = 1, level_id = new_ID);
        here.fwd_dir = True;
        visit [-:play:level_id==new_ID:->];
    } else {
        new_ID = str(1) + "_" + str(random.randint(1000, 9000));
        self +:play:level_id=new_ID:+> level(game_level = 1, level_id = new_ID);
        print(":-: Visiting Intro Screen | Created Level ID :", new_ID);
        here.fwd_dir = True;
        visit [-:play:level_id==new_ID:->];

    }
}

:node:start_screen:can:exit_game {
    if here.g.running == False {
        pygame.quit();
        sys.exit();
        disengage;
    }
}