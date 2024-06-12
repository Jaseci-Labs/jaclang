<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://www.jac-lang.org//assets/logo.png">
    <source media="(prefers-color-scheme: light)" srcset="https://www.jac-lang.org//assets/logo.png">
    <img alt="Jaclang Programming Language: Unique and Powerful programming language that runs on top of Python"
         src="https://www.jac-lang.org//assets/logo.png"
         width="20%">
  </picture>

[Jac Website] | [Getting started] | [Learn] | [Documentation] | [Contributing]

  [![PyPI version](https://img.shields.io/pypi/v/jaclang.svg)](https://pypi.org/project/jaclang/) [![Tests](https://github.com/chandralegend/jaclang/actions/workflows/run_pytest.yml/badge.svg?branch=main)](https://github.com/chandralegend/jaclang/actions/workflows/run_pytest.yml) [![codecov](https://codecov.io/github/chandralegend/jaclang/graph/badge.svg?token=OAX26B0FE4)](https://codecov.io/github/chandralegend/jaclang)
</div>

This is the main source code repository for the [Jac] programming language. It contains the compiler, language server, and documentation.

[Jac]: https://www.jac-lang.org/
[Jac Website]: https://www.jac-lang.org/
[Getting Started]: https://www.jac-lang.org//start/
[Learn]: https://www.jac-lang.org//learn
[Documentation]: https://www.jac-lang.org//learn/guide/
[Contributing]: .github/CONTRIBUTING.md

## What and Why Jac?

- **Native Superset of Python** - Jac is a native superset of python, meaning the entire python ecosystem is directly interoperable with Jac without any trickery (no interop interface needed). Like Typescript is to Javascript, or C++ is to C, Jac is to Python. (every Jac program can be ejected to pure python, and every python program can be transpiled to a Jac program)

- **AI as a Programming Language Constructs** - Jac includes a novel (neurosymbolic) language construct that allows replacing code with generative AI models themselves. Jac's philosophy abstracts away prompt engineering. (Imagine taking a function body and swapping it out with a model.)

- **New Modern Abstractions** - Jac introduces a paradigm that reasons about persistence and the notion of users as a language level construct. This enables writing simple programs for which no code changes are needed whether they run in a simple command terminal, or distributed across a large cloud. Jac's philosophy abstracts away dev ops and container/cloud configuration.

- **Jac Improves on Python** - Jac makes multiple thoughtful quality-of-life improvements/additions to Python. These include new modern operators, new types of comprehensions, new ways of organizing modules (i.e., separating implementations from declarations), etc.


## Quick Start

To install Jac, run:

```bash
pip install jaclang
```
Run `jac` in the terminal to see whether it is installed correctly.

Read ["Getting Started"] from [Docs] for more information.

["Getting Started"]:https://www.jac-lang.org//start/
[Docs]: https://www.jac-lang.org//learn/guide/

## Installing from Source

If you really want to install from source (though this is not recommended), see
[INSTALL.md](support/INSTALL.md).

## Getting Help

Submit and issue! Community links coming soon.

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## License

Jaclang is distributed under the terms of both the MIT license with a few other open source projects vendored
within with various other licenses that are very permissive.

See [LICENSE-MIT](.guthub/LICENSE), and
[COPYRIGHT](COPYRIGHT) for details.

## Trademark

[Jaseci][jaseci] owns and protects the Jaclang trademarks and logos (the "Jaclang Trademarks").

If you want to use these names or brands, please read the [media guide][media-guide].

Third-party logos may be subject to third-party copyrights and trademarks. See [Licenses][policies-licenses] for details.

[jaseci]: https://jaseci.org/
[media-guide]: https://jaseci.org/policies/logo-policy-and-media-guide/
[policies-licenses]: https://www.jaseci.org/policies/licenses