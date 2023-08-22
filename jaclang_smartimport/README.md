# jaclang_smartimport

`jaclang_smartimport` is a plugin for the `jaclang` programming language that provides enhanced module importing capabilities. It allows for asynchronous module loading, ensuring that your `jaclang` applications run efficiently and smoothly.

## Features

- **Asynchronous Module Loading**: Load modules in a separate process, preventing any blocking in the main application.
- **Timeouts**: Set a timeout for module loading, ensuring that your application doesn't hang indefinitely.
- **Error Handling**: Gracefully handle any errors that occur during module loading.

## Installation

To install `jaclang_smartimport`, you can use pip:

```bash
pip install jaclang_smartimport
```

## Usage

Once installed, `jaclang_smartimport` will automatically integrate with `jaclang` and override the default `jac_red_import` function.

## Development

To contribute to `jaclang_smartimport`, clone the repository and install the required dependencies:

```bash
git clone <repository_url>
cd jaclang_smartimport
pip install -r requirements.txt
```

Make your changes and submit a pull request!

