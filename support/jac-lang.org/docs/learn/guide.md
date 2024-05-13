# Jac Coding Manual

Jac is a powerful Python-based language that gives coders wings. Let's dive right in! If you haven't already installed Jaclang, you can find the installation guide [here](../start/installation.md).

## A Complete Example

We will begin this journey from the top down. We will examine a simple yet complete program in Python, as well as two Jac versions. The first version closely resembles Python in its module implementation, while the second version showcases the clean and efficient Jactastic way of implementing the same functionality. First, we will take a look at the complete examples, and then break them down into smaller parts.

=== "Python (circle.py)"
    ```python linenums="1"
    --8<-- "examples/manual_code/circle.py"
    ```
=== "Jac (circle.jac)"
    ```jac linenums="1"
    --8<-- "examples/manual_code/circle.jac"
    ```
=== "circle_clean.jac"
    ```jac linenums="1"
    --8<-- "examples/manual_code/circle_clean.jac"
    ```
=== "circle_clean_impl.jac"
    ```jac linenums="1"
    --8<-- "examples/manual_code/circle_clean_impl.jac"
    ```

Now lets break it down!

### Docstrings

Jac docstrings have the same syntax as Python docstrings. However, it's important to note that Jac docstrings can only be used as docstrings and not as comments. This means that there are only a few places where you can use them. You can place them at the **top of a module, before the declaration of functions, methods, classes (archetypes), global variable statements, and module level code blocks** (for example, `with entry {}` style blocks). It's also important to note that the docstring should be placed **before the function call**. This is done to improve code readability, especially when a large docstring is used.


=== "Jac"
    ```jac linenums="1"
    --8<-- "examples/manual_code/circle.jac::8"
    ```
=== "Python"
    ```python linenums="1"
    --8<-- "examples/manual_code/circle.py::11"
    ```

### Multiline Comments

Jac does not allow docstrings to be used as comments. However, it provides an elegant way to specify multiline comments. Any text between `#*` and `*#` is treated as a multi-line comment. This is delightfully Pythontic.

=== "Jac"
    ```jac linenums="15"
    --8<-- "examples/manual_code/circle.jac:15:18"
    ```
=== "Python"
    ```python linenums="18"
    --8<-- "examples/manual_code/circle.py:19:23"
    ```


### Imports

Import statements in JAC are quite similar to Python. However, it's important to note that while importing a Python module, you need to use `import:py`, and for a JAC module, `import:jac`. The module paths and other details are very similar to that of Python.

Quick note on `from import`, they work like this.

=== "Jac"
    ```jac
    import:py from os, getcwd, listdir, path
    ```
=== "Python"
    ```python
    from os import getcwd, listdir, path
    ```

The reason for this change is purely aesthetic - when reading a file with many imports, it looks better to have all the import keywords at the beginning.


### Globals

### Abilities (Functions)

In Jac, a new naming convention has been introduced to refer to functions and data spatial code blocks as "abilities." While we will discuss data spatial programming in more detail later on, for now, it's worth noting that the functions in Python and Jac are quite similar, except that the `def` keyword is replaced with `can`. Additionally, Jac requires that type hints be included in function signatures (both for parameters and return values). Any function that doesn't include a return signature (i.e., `-> TYPE`) is assumed to be `-> None` by default.

=== "circle.jac"
    ```jac linenums="10"
    --8<-- "examples/manual_code/circle.jac:10:13"
    ```
=== "circle.py"
    ```python linenums="13"
    --8<-- "examples/manual_code/circle.py:14:16"
    ```

### Enumeration

Jac includes enums as a language feature. Currently, the semantics of this enum are simple, but they will evolve over time. If needed, you can import Enum to leverage Python's path. However, it's important to note that you'll have to use Jac's keyword escape feature to avoid a syntax error when referring to the enum package.

```jac
import:py from enum, Enum, auto;
```
If you try to import from enum this way in jac, you'll get a syntax error.


```jac
import:py from <>enum, Enum, auto;
```
This is the way to import from enum. Any language level keyword can be escaped by putting a `<>` immediately before the keyword.

=== "Jac"
    ```jac linenums="20"
    --8<-- "examples/manual_code/circle.jac:20:24"
    ```
=== "Python"
    ```python linenums="25"
    --8<-- "examples/manual_code/circle.py:26:30"
    ```

### Shape Class

This is an example of a Shape class in Jac. A couple things to note here.

=== "Jac"
    ```jac linenums="26"
    --8<-- "examples/manual_code/circle.jac:26:32"
    ```
=== "Python"
    ```python linenums="32"
    --8<-- "examples/manual_code/circle.py:33:42"
    ```

### Circle Class

=== "Jac"
    ```jac linenums="34"
    --8<-- "examples/manual_code/circle.jac:34:45"
    ```
=== "Python"
    ```python linenums="43"
    --8<-- "examples/manual_code/circle.py:45:54"
    ```

### Script handling

=== "Jac"
    ```jac linenums="47"
    --8<-- "examples/manual_code/circle.jac:47:53"
    ```
=== "Python"
    ```python linenums="55"
    --8<-- "examples/manual_code/circle.py:57:65"
    ```

### Tests

=== "Jac"
    ```jac linenums="55"
    --8<-- "examples/manual_code/circle.jac:55:59"
    ```
=== "Python"
    ```python linenums="66"
    --8<-- "examples/manual_code/circle.py:68:81"
    ```

### Clean Approach

=== "circle_clean.jac"
    ```jac linenums="1"
    --8<-- "examples/manual_code/circle_clean.jac"
    ```
=== "circle_clean_impl.jac"
    ```jac linenums="1"
    --8<-- "examples/manual_code/circle_clean_impl.jac"
    ```
=== "circle_clean_tests.jac"
    ```jac linenums="1"
    --8<-- "examples/manual_code/circle_clean_tests.jac"
    ```


## Complete list of Differences and Features beyond Python

Jac is a programming language that includes all of Python 3's features and full native compatibility. However, each of the features  and adjustments described here represents Jac's approach to improve programmer effectiveness in a way that is distinct from Python. These choices were made focusing on type safety, readability, expressiveness, and general code ninja goodness. As the Jac language evolves, these features will be refined and expanded based on user feedback, practical usage, and the evolution of python and coding in general.

Additionally, Jac is the first language to implement the data spatial object paradigm. After getting used to Jac, we encourage every coder to expand their toolkit with this powerful programming model.

### Whitespace doesn't matter

In contrast to Python, which relies on indentation to define code blocks, Jac does not use whitespace for this purpose. This gives programmers have more flexibility in formatting their code, but it is still recommended to maintain a consistent style for readability purposes. More beautiful formatting styles are possible with increased flexibility in code layout.


```jac linenums="1"
--8<-- "examples/micro/whitespace.jac"
```

### Types hints are required

In Jac, you are required to use type hints for specific variable declarations and function signatures. This ensures type safety, improves code self-documentation and aids in debugging and maintaining the codebase.

```jac linenums="1"
--8<-- "examples/micro/type_hints.jac"
```

### Typing library implicitly available

Jac has an inbuilt typing system that is similar to Python's typing library. However, it's implicitly available, which means you don't need to import any typing modules explicitly to use features such as `List`, `Dict`, `Optional`, etc. You can easily reference them with a backtick as  `` `List ``, `` `Dict ``, and `` `Optional ``.

### Can separate definitions from declarations

=== "Ability"
    ```jac linenums="1"
    --8<-- "examples/micro/decl_defs.jac:3:12"
    ```
=== "Class Method"
    ```jac linenums="1"
    --8<-- "examples/micro/decl_defs.jac:14:25"
    ```
=== "Another"
    ```jac linenums="1"
    --8<-- "examples/micro/separate_defs.jac"
    ```
=== "Traditional"
    ```jac linenums="1"
    --8<-- "examples/micro/decl_defs.jac:27:41"
    ```


In Jac, separating the declaration of functions or variables from their definitions contributes to a cleaner code structure, where the high-level structure and relationships between different parts of the code are immediately apparent. This approach simplifies navigation through code, especially in large projects, as it enables developers to quickly understand the code architecture without getting bogged down in implementation details from the outset.

### Can have definitions and implementations span multiple files

Jac offers the option to divide code definitions from their corresponding implementations and store them in different files. This approach improves code modularity and maintainability by allowing developers to organize their codebase more efficiently. The definitions, such as abstract declarations or interfaces, can be placed in one file, while their implementations can be stored in separate files. By separating the definitions from their implementations, it becomes easier to manage the codebase, especially for large-scale projects, and encourages team collaboration. This structure also facilitates concurrent work by different team members on different parts of the implementation without conflicts, as the interface remains consistent and shared across the team. Additionally, this approach results in clear version control and change tracking, making the development process more efficient and less prone to errors.

=== "decl_defs_main.jac"
    ```jac linenums="1"
    --8<-- "examples/micro/decl_defs_main.jac"
    ```
=== "decl_defs_impl.jac"
    ```jac linenums="1"
    --8<-- "examples/micro/decl_defs_impl.jac"
    ```

### Proper access control

In Jac, the access control is more precise and explicit, compared to Python. Jac introduces access modifiers that are similar to those found in languages like Java or C#. This allows for defining access levels such as `public`, `private`, and `protected`. This feature enhances encapsulation and helps developers to define the scope of class members more clearly. By controlling access to the internals of a class, programmers can prevent unintended interactions with the class's methods and attributes, leading to more stable and maintainable code.

```jac linenums="1"
--8<-- "examples/micro/access_info.jac"
```

### Proper abstract classes/methods

Jac comes with built-in support for abstract classes and methods, which is implemented through the `abc` module in Python. In Jac, defining an abstract class is more intuitive, and abstract methods can be declared directly. This ensures that derived classes must implement the abstract methods, which promotes consistency and predictability in class hierarchies. The proper implementation of abstract classes and methods in Jac makes it easier to design and work with complex object-oriented systems, as it provides a clear framework for structuring and interacting with classes.

```jac linenums="1"
--8<-- "examples/micro/class_multi_inherit.jac"
```

### Tuples are explicit
Tuples in Jac must be explicitly declared, which differs from Python's implicit tuple creation. This design choice avoids accidental creation of tuples, enhancing code clarity.

### Docstrings in the right place
Docstrings in Jac are placed differently compared to Python. This change is aimed at improving readability and making the documentation process more intuitive and consistent.

### Elvis Operator
Jac introduces the Elvis operator (`?:`), which is a shorthand for an if-else statement, similar to the ternary operator in other languages. It provides a more concise way to write conditional expressions.

### Null Safe Operator
The Null Safe operator in Jac allows safe access to an object's properties or methods without the risk of encountering a null reference error. This operator helps in writing cleaner, more robust code.

### Filter Comprehension
Filter comprehension in Jac is a built-in feature that provides a more intuitive and concise way to filter collections, similar to list comprehensions in Python but with a focus on filtering.

### Assign Comprehension
Assign comprehension is a unique feature in Jac that allows for direct assignment within a comprehension, making certain patterns of data processing more succinct and readable.

### Dataclass style basis for OOP
Jac's approach to object-oriented programming is based on a dataclass style, where classes are primarily used to store data. This makes data handling more straightforward and efficient.

### Abstract Classes, Methods and overrides built in

### Application Bundling

### Proper multiline Comments
Multiline comments in Jac are more versatile and user-friendly compared to Python. This feature enhances the ability to document code extensively without resorting to string literals or consecutive single-line comments.

### Explicit notation for special variables
Special variables in Jac have explicit notations, making it clear when such variables are being used. This feature aids in code readability and helps avoid accidental misuse of these variables.

### No need for gratuitous self usage
In Jac, there is no need to use the `self` keyword in all class method signatures as in Python. This design choice simplifies method definitions and makes the code cleaner and easier to read.

### Optional Left to right Pipe style expressivity
Jac offers an optional left-to-right pipe-style syntax for function calls, similar to the Unix pipeline or functional programming languages. This feature allows for more expressive and readable code, especially when chaining multiple function calls.

### Full Support of Data Spatial Programming Paradigmn
More on this soon!!!
