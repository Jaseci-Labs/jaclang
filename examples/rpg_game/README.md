# Converting a python Role Playing Game to ```Jaclang```

This document is to serve as a discription for each RPG implementations which were done iteratively to visualize the changes made when converting to Jaclang.

> An in depth tutorial is available [here](./RPG_DSP_journey.md).

## Pure Python implementation : [python_impl](./python_impl/)

This is a role playing game built using the pygame library in the python language. The game is inspired by a game tutorial available on _YouTube_ available [here](<https://www.youtube.com/playlist?list=PLkkm3wcQHjT7gn81Wn-e78cAyhwBW3FIc>).

## Pylang or Jacthon? : [jac_impl_1](./jac_impl/jac_impl_1/)

This is the first implementation of the python RPG in Jaclang. In this implementation the python code is one-to-one mapped into Jaclang.

![Py vs Jac_1](./Diagrams/Jac_impl_1_comparison.png)

Here there are no significant changes are required for the code structure other than the Jaclang syntax.

## Less Py more Jac : [jac_impl_2](./jac_impl/jac_impl_2/)

In this iteration of the jac implementation for the RPG, some of the unique features of Jaclang, such as ```has``` variables, were explored. This feature allows for definitions of fields which will self initialize with an auto geneerate ```init```. Furthermore, previously dynamically typed variables has been updated with type annotations.

![Jac_1 Vs Jac_2](./Diagrams/Jac_impl_2_comparison.png)

## Jactastic Wonderland : [jac_impl_3](./jac_impl/jac_impl_3/)

This is where we brought out the big guns. Jaclang has a feature where a function definition and its implementation can be coded at two different locations, as long as the .jac files are included on the execution code. This feature allows a cleaner function definition which can make sense without looking at their tedious implementations. Here is a small example of the feature.

![Jac_2 Vs Jac3](./Diagrams/Jac_impl_3_comparison.png)

Another change made was that ```init``` functions has been completely removed from the codebase which means only auto generated initialization functions are used using ```has``` variables. However, as there are requirements to run some initialization operations ```postinit``` function is used which will run at the end of the auto generated ```init```.

## Data-Spatial Programming! : [jac_impl_4](./jac_impl/jac_impl_4/)

This implementation is the BOMB! This is the first ever game written in a data-spatial architecture where each level is a node on a graph while the game itself is a walker, traversing on the graph.

![DSP](./Diagrams/RPG%20Space%20-%20DSP.png)

Without making significant changes to the existing codebase in [jac_impl_3](./jac_impl/jac_impl_3/) a new DSP.jac file is introduces which includes the data-spatial architecture and runtime logic.

## LLM Generating Maps! : [jac_impl_5](./jac_impl/jac_impl_5/)

If the previous version was the BOMB this implementation would be an ICBM. This is a replica of [jac_impl_4](./jac_impl/jac_impl_4/) with an addition AI based map generation feature. This simple game is the world's first game having procedurally generated maps using LLMs based on previous gameplays. This specific implementation requires an OpenAI API key to operate which will generate playable maps using 'gpt-4'.
