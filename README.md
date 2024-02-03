# Gaphas
[![Build state](https://github.com/gaphor/gaphas/workflows/build/badge.svg)](https://github.com/gaphor/gaphas/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/e9837cc647b72119fd11/maintainability)](https://codeclimate.com/github/gaphor/gaphas/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/e9837cc647b72119fd11/test_coverage)](https://codeclimate.com/github/gaphor/gaphas/test_coverage)
![Docs build state](https://readthedocs.org/projects/gaphas/badge/?version=latest)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat)](https://github.com/RichardLitt/standard-readme)
[![Matrix](https://img.shields.io/badge/chat-on%20Matrix-success)](https://matrix.to/#/#gaphor_Lobby:gitter.im)
[![All Contributors](https://img.shields.io/badge/all_contributors-9-orange.svg?style=flat-square)](#contributors)

> Gaphas is the diagramming widget library for Python.

![Gaphas Demo](https://raw.githubusercontent.com/gaphor/gaphas/main/docs/images/gaphas-demo.gif)

Gaphas is a library that provides the user interface component (widget) for drawing diagrams. Diagrams can be drawn to screen and then easily exported to a variety of formats, including SVG and PDF. Want to build an app with chart-like diagrams? Then Gaphas is for you! Use this library to build a tree, network, flowchart, or other diagrams.

This library is currently being used by [Gaphor](https://github.com/gaphor/gaphor) for UML drawing,
[RAFCON](https://github.com/DLR-RM/RAFCON) for state-machine based robot control, and [ASCEND](http://ascend4.org/) for solving mathematical models.

## 📑 Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## 📜 Background

Gaphas was built to provide the foundational diagramming portions of [Gaphor](https://github.com/gaphor/gaphor). Since Gaphor is built on GTK and Cairo, [PyGObject](https://pygobject.readthedocs.io/) provides access to the GUI toolkit and [PyCairo](https://pycairo.readthedocs.io/) to the 2D graphics library. However, there wasn't a project that abstracted these technologies to easily create a diagramming tool. Hence, Gaphas was created as a library to allow others to create a diagramming tool using GTK and Cairo.

Here is how it works:

- Items (Canvas items) can be added to a Canvas.
- The Canvas maintains the tree structure (parent-child relationships between items).
- A constraint solver is used to maintain item constraints and inter-item constraints.
- The item (and user) should not be bothered with things like bounding-box calculations.
- Very modular--e.g., handle support could be swapped in and swapped out.
- Rendering using Cairo.

The main portions of the library include:

- canvas - The main canvas class (container for Items).
- items - Objects placed on a Canvas.
- solver - A constraint solver to define the layout and connection of items.
- gtkview - A view to be used in GTK applications that interacts with users with tools.
- painters - The workers used to paint items.
- tools - Tools are used to handle user events (such as mouse movement and button presses).
- aspects - Provides an intermediate step between tools and items.

Gaphas contains default implementations for `Canvas` and `Item`s. There are protocols in place
to allow you to make your own canvas.

## 💾 Install

To install Gaphas, simply use pip:

```bash
$ pip install gaphas
```

Use of a
[virtual environment](https://virtualenv.pypa.io/en/latest/) is highly recommended.

### Development

To setup a development environment with Linux:

```bash
$ sudo apt-get install -y python3-dev python3-gi python3-gi-cairo
    gir1.2-gtk-3.0 libgirepository1.0-dev libcairo2-dev
$ pip install poetry
$ poetry install
```

## 🔦 Usage

API docs and tutorials can be found on [Read the Docs](https://gaphas.readthedocs.io).

## ♥ Contributing

Thanks goes to these wonderful people ([emoji key](https://github.com/kentcdodds/all-contributors#emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore -->
<table><tr><td align="center"><a href="https://github.com/amolenaar"><img src="https://avatars0.githubusercontent.com/u/96249?v=4" width="100px;" alt="Arjan Molenaar"/><br /><sub><b>Arjan Molenaar</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/commits?author=amolenaar" title="Code">💻</a> <a href="https://github.com/gaphor/gaphas/issues?q=author%3Aamolenaar" title="Bug reports">🐛</a> <a href="https://github.com/gaphor/gaphas/commits?author=amolenaar" title="Documentation">📖</a> <a href="#review-amolenaar" title="Reviewed Pull Requests">👀</a> <a href="#question-amolenaar" title="Answering Questions">💬</a> <a href="#plugin-amolenaar" title="Plugin/utility libraries">🔌</a></td><td align="center"><a href="https://ghuser.io/danyeaw"><img src="https://avatars1.githubusercontent.com/u/10014976?v=4" width="100px;" alt="Dan Yeaw"/><br /><sub><b>Dan Yeaw</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/commits?author=danyeaw" title="Code">💻</a> <a href="https://github.com/gaphor/gaphas/commits?author=danyeaw" title="Tests">⚠️</a> <a href="#review-danyeaw" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/gaphor/gaphas/issues?q=author%3Adanyeaw" title="Bug reports">🐛</a> <a href="#question-danyeaw" title="Answering Questions">💬</a> <a href="#infra-danyeaw" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/gaphor/gaphas/commits?author=danyeaw" title="Documentation">📖</a></td><td align="center"><a href="https://github.com/wrobell"><img src="https://avatars2.githubusercontent.com/u/105664?v=4" width="100px;" alt="wrobell"/><br /><sub><b>wrobell</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/commits?author=wrobell" title="Code">💻</a> <a href="https://github.com/gaphor/gaphas/commits?author=wrobell" title="Tests">⚠️</a> <a href="#review-wrobell" title="Reviewed Pull Requests">👀</a></td><td align="center"><a href="https://github.com/jlstevens"><img src="https://avatars3.githubusercontent.com/u/890576?v=4" width="100px;" alt="Jean-Luc Stevens"/><br /><sub><b>Jean-Luc Stevens</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/commits?author=jlstevens" title="Code">💻</a> <a href="https://github.com/gaphor/gaphas/issues?q=author%3Ajlstevens" title="Bug reports">🐛</a> <a href="https://github.com/gaphor/gaphas/commits?author=jlstevens" title="Documentation">📖</a></td><td align="center"><a href="http://www.franework.de"><img src="https://avatars1.githubusercontent.com/u/1144966?v=4" width="100px;" alt="Franz Steinmetz"/><br /><sub><b>Franz Steinmetz</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/commits?author=franzlst" title="Code">💻</a> <a href="https://github.com/gaphor/gaphas/issues?q=author%3Afranzlst" title="Bug reports">🐛</a></td><td align="center"><a href="https://github.com/adrianboguszewski"><img src="https://avatars3.githubusercontent.com/u/4547501?v=4" width="100px;" alt="Adrian Boguszewski"/><br /><sub><b>Adrian Boguszewski</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/commits?author=adrianboguszewski" title="Code">💻</a></td><td align="center"><a href="https://github.com/Rbelder"><img src="https://avatars3.githubusercontent.com/u/15119522?v=4" width="100px;" alt="Rico Belder"/><br /><sub><b>Rico Belder</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/issues?q=author%3ARbelder" title="Bug reports">🐛</a> <a href="#review-Rbelder" title="Reviewed Pull Requests">👀</a></td></tr><tr><td align="center"><a href="http://www.boduch.ca"><img src="https://avatars2.githubusercontent.com/u/114619?v=4" width="100px;" alt="Adam Boduch"/><br /><sub><b>Adam Boduch</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/issues?q=author%3Aadamboduch" title="Bug reports">🐛</a></td><td align="center"><a href="https://github.com/janettech"><img src="https://avatars3.githubusercontent.com/u/13398384?v=4" width="100px;" alt="Janet Jose"/><br /><sub><b>Janet Jose</b></sub></a><br /><a href="https://github.com/gaphor/gaphas/commits?author=janettech" title="Documentation">📖</a></td></tr></table>

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/kentcdodds/all-contributors) specification. Contributions of any kind are welcome!

1. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug.
    There is a [first-timers-only](https://github.com/gaphor/gaphas/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Afirst-timers-only) tag for issues that should be ideal for people who are not very familiar with the codebase yet.
2. Fork [the repository](https://github.com/gaphor/gaphas) on GitHub to    start making your changes to the **main**       branch (or branch off of it).
3. Write a test which shows that the bug was fixed or that the feature
   works as expected.
4. Send a pull request and bug the maintainers until it gets merged and
   published. :smile:

See [the contributing file](CONTRIBUTING.md)!

## © License

Copyright © Arjan Molenaar and Dan Yeaw

Licensed under the [Apache License 2.0](LICENSES/Apache-2.0.txt).

Summary: You can do what you like with Gaphas, as long as you include the required notices. This permissive license contains a patent license from the contributors of the code.
