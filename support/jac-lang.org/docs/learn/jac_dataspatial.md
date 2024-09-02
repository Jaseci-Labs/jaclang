# Data Spatial Programming with Jaclang

It's interesting to see how much programming languages have progressed over the years. However, one essential data structure, graphs, has not received much attention. Almost every data structure used by programmers, such as stacks, lists, queues, trees, and heaps, can be described as a type of graph, except for hash tables. Despite this, no programming language has welcomed graphs as its primary data representation.

Graphs are easy for humans to understand, which makes them great for solving computational problems, especially in fields like AI. Some people say that current graph libraries in their favorite programming languages are good enough, so there's no need for a language focused on graphs. However, programming languages are based on their main ideas, and since graphs aren't a fundamental part of these languages, they are not designed for the detailed meanings that graphs offer.

One concern is that if graphs become the main way data is organized, it could make the language slower. However, many modern languages already use complex ways of organizing data, like dynamic typing, which can slow down the program when it runs. Jaclang wants to change how we think about data and memory by using graphs as the foundation for memory representation, because they naturally have a lot of meaning and information.

We make follwoing assumptions about graphs in Jaclang;

* Graphs are directed and can also be used as undirected with a special type of doubly directed edge.
* It's important to note that both nodes and edges have their own distinct identities. For instance, an edge is not a pairing of two nodes. This is important because both nodes and edges can have contexts.
* You can have multiple edges between the same pair of vertices, and can also have edges that start and end at the same vertex (self-loop edges). 
* Your graphs can have cycles. Not required to be acylic.
* No hypergraphs.

Refer to [Wikipedia description of graphs](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)) to learn more about graphs.

## Nodes

In Jaclang data spatial programming nodes are important concept. There are two types of nodes;

* **Root Node**: It is the starting point of the graph and is a built-in node type. Each graph can have only one root node.
* **Generic Node**:  It is a built-in node type that can be used throughout the Jaseci application. You can customize the name and properties of this node type as well.

Here's and example code snippet to create a node:

```
node city{
    has name:str;
    has location:tupple;

    can welcome with entry{
        print("Welcome to ", name);
    }
}
```

In a Jaclang, we can define variables in a node using the `has` keyword. Moreover, we can set default values for variables. For instance, we could set name to have a default value of michigan with `has name:str = michigan`.

## Edges

In Jaclang, edges are an important part of the graph structure. They create  relationships between nodes. Just like nodes, you can customize edge types with variables, offering more flexibility in building the graph structure.

Edges can have specific behaviors or conditions attached to them, which trigger particular actions or behaviors in the program. For instance, the custom edge mentioned earlier, the intent_transition edge type, is designed to move between states based on a user's input intent. This type of edge behavior is extremely useful for developing natural language processing (NLP) applications, where the system needs to understand and interpret user input.

By using custom edge types with specific behaviors, you can make your code more modular, easier to read and maintain, and add more functionality to your applications. Additionally, by using edges, you can create more complex relationships between nodes, which can be used to create more complex traversal patterns through the graph structure. Overall, edges in Jaseci are a powerful tool that can be used to create more complex, intelligent, and versatile applications.

Here is a example of creating a edge in Jaclang;

```
edge road{
    has distance:float;
}
```

Like nodes, edges also can have variables. Similarly variables inside edges also treated as variables inside nodes.

### Operators for connecting nodes

In Jaseci, specific operators are used to connect nodes and edges to form graphs;

* `++>`

This operator is used to connect two nodes in a forward direction. For example, `root ++> node1` will connect root to node1. See the code snippet and the expected graph in the following example.


* `+:name_of_edge:+>`

This operator is used to connect two nodes with custom type of edge in forward direction. for example `city_a +:road:+> city_b` will connect `city_a` and `city_b` with edge `road`.

* `<++>`

This operator is used to connect two nodes in a backward direction. For example, `node2 <++> node1` will connect node2 to node1 with a bidirectional edge.


* `<+:name_of_edge:+>`

This operator is used to connect two nodes with custom type of edge in backward direction. for example `city_a <+:road:+> city_b` will connect `city_a` and `city_b` with edge `road`.


* `+:name_of_edge(variable_declared = some_value):+>`

This operator is used to connect two nodes in a forward direction with a custom edge type that has a variable declared with a specific value. For example, `city_a +: road(distance=15) :+> city_b;` will connect city_a to city_b with a custom edge type named `road` and a variable `distance` declared with the value `15`.


* `<+:name_of_edge(variable_declared = some_value):+>`

This operator is used to connect two nodes in a backward direction with a custom edge type that has a variable declared with a specific value. For example, `city_a <+: road(distance=15) :+> city_b;` will connect `city_a` to `city_b` with a custom edge type named `road` and a variable `distance` declared with the value `15`.

You can use these operators to create detailed graphs with customized edge types that can hold specific values. This helps you build a network of nodes to represent complex data structures like trees or graphs. Customized edge types also let you define specific behavior for different types of connections between nodes.

### Creating Graphs Examples

Graphs can be created by connecting multiple nodes with edges. This is done using the connect operator ++> <++>.

```
walker creator {
    can create with `root entry { 
        city_a = city(name="City A", location=(10.0, 20.0));
        city_b = city(name="City B", location=(10.1, 20.1));
        city_c = city(name="City C", location=(10.2, 20.2));

        end=root;
        end++>(end:=[city_a]);
        end++>(end:=[city_b]);
        end++>(end:=[city_c]);

        # Create roads between cities and landmarks
        city_a <+: road(distance=15) :+> city_b;
        city_a <+: road(distance=20) :+> city_c;
    }
}
```

The code shown above creates the structure of the graph. The spawn keyword is used to begin the creation of nodes and edges,

```
with entry {
    print("Welcome to City Traffic!");
    root spawn creator();

    d1=dotgen();
    l1=d1|>len;
    print(d1);

    }

```

You can visualize this graph using streamlit;

```bash
jac graph_example.jac
```

### Referencing and Dereferencing Nodes and Edges

### Plucking values from nodes and edges

## Walkers





