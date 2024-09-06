# Contributing to MTLLM Documentation
## Running a local preview instance of the documentation

To open a preview of the codedoc server locally, following steps should be followed.

1. Make sure Node.js is properly installed on your linux system.

    ```bash
    curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
    sudo apt-get install -y nodejs
    ```

2. install codedoc cli and required packages.

    ```bash
    cd docs
    npm i -g @codedoc/cli
    codedoc install
    ```
4. Initiate the codedoc server

    ```bash
    codedoc serve
    ```

3. When prompted open the server from a web browser or the VS Code editor itself.

    >    Default - http://localhost:3000/mtllm