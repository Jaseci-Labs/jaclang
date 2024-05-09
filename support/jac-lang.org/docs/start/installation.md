# **Installing Jac-Lang**

- Firstly make sure that this prerequisite is fulfilled.
    - Python 3.12 or higher

- It is recommended to use a Python environment when installing and running Jac Lang. You can simply follow these steps to set up your environment:
    - Open a Linux bash terminal. [It is recommended to use WSL (Windows Subsystem for Linux) if you are a windows OS user.]

    - Create a virtual environment with Python version 3.12 or higher. Feel free to use your own environment name here.

    ```bash
    conda create -n <env_name> python=3.12 -y
	conda activate <env_name>
    ```
    - Now you can simply install Jac Lang using pypi.

    ```bash
    python -m pip install -U jaclang
    ```
> **Note:**
>
> If you have installed Jac Lang a while back, it may be outdated due to frequent updates. Ensure you have the latest Jac Lang version by executing the same command.

Once you've got Jaclang installed, just give the Jac CLI a try to make sure everything's up and running smoothly.

- Start the Jac CLI:
    ```bash
    jac
    ```
- Run a .jac file
    ```bash
    jac run <file_name>.jac
- To test run a 'Hello World'Program
    ```bash
    echo "with entry { print('hello world'); }" > test.jac;
    jac run test.jac;
    rm test.jac;
    ```
> **Note**
>
> If these commands prints ```hello world``` you are good to go.

## Supportive Jac CLI commands

- Clean cached files (recommended after each run):
    ```bash
    jac clean
    ```
- Print the data-spatial graph to a file and visualize it using [Graphviz](https://dreampuf.github.io/GraphvizOnline/):
    ```bash
    jac dot <file_name>.jac
    ```
    - Visit [https://dreampuf.github.io/GraphvizOnline/](https://dreampuf.github.io/GraphvizOnline/) to visualize the graph.

## Installing the VS Code Extention

In addition to setting up JacLang itself, you may also want to take advantage of the JacLang language extension for Visual Studio Code (VSCode). This will give you enhanced code highlighting, autocomplete, and other useful language features within your VSCode environment.

- To install just visit the VS Code marketplace and install,
    - [Jac Analyzer](https://marketplace.visualstudio.com/items?itemName=jaseci-labs.jaclang-extension)