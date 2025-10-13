<!-- Banner -->
![alt Banner of the odp köln package](https://raw.githubusercontent.com/klaasnicolaas/python-koeln/main/assets/header_koeln-min.png)

<!-- PROJECT SHIELDS -->
[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE)

[![GitHub Activity][commits-shield]][commits-url]
[![PyPi Downloads][downloads-shield]][downloads-url]
[![GitHub Last Commit][last-commit-shield]][commits-url]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

[![Build Status][build-shield]][build-url]
[![Typing Status][typing-shield]][typing-url]
[![Code Coverage][codecov-shield]][codecov-url]

Asynchronous Python client for the open datasets of Köln (Germany).

## About

A python package with which you can retrieve data from the Open Data Platform of Köln via [their API][api]. This package was initially created to only retrieve parking data from the API, but the code base is made in such a way that it is easy to extend for other datasets from the same platform.

## Installation

```bash
pip install koeln
```

## Datasets

You can read the following datasets with this package:

- [Disabled parking spaces / Behindertenparkplätze][disabled_parkings] (441 locations)

<details>
    <summary>Click here to get more details</summary>

### Disabled parking spaces

| Variable | Type | Description |
| :------- | :--- | :---------- |
| `entry_id` | integer | The ID for the parking location |
| `number` | integer | The number of the parking spaces on this location |
| `district` | string | The district name where the parking location is located |
| `district_nr` | integer | The district number where the parking location is located |
| `note` | string | A note about the parking location |
| `longitude` | float | The longitude of the parking location |
| `latitude` | float | The latitude of the parking location |
</details>

## Example

```python
import asyncio

from koeln import StadtKoeln


async def main() -> None:
    """Show example on using the API of Köln."""
    async with StadtKoeln() as client:
        disabled_parkings = await client.disabled_parkings()
        print(disabled_parkings)


if __name__ == "__main__":
    asyncio.run(main())
```

## Use cases

[NIPKaart.nl][nipkaart]

A website that provides insight into where disabled parking spaces are, based
on data from users and municipalities. Operates mainly in the Netherlands, but
also has plans to process data from abroad.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up development environment

The simplest way to begin is by utilizing the [Dev Container][devcontainer]
feature of Visual Studio Code or by opening a CodeSpace directly on GitHub.
By clicking the button below you immediately start a Dev Container in Visual Studio Code.

[![Open in Dev Containers][devcontainer-shield]][devcontainer]

This Python project relies on [Poetry][poetry] as its dependency manager,
providing comprehensive management and control over project dependencies.

You need at least:

- Python 3.11+
- [Poetry][poetry-install]

### Installation

Install all packages, including all development requirements:

```bash
poetry install
```

_Poetry creates by default an virtual environment where it installs all
necessary pip packages_.

### Pre-commit

This repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. To setup the pre-commit check, run:

```bash
poetry run pre-commit install
```

And to run all checks and tests manually, use the following command:

```bash
poetry run pre-commit run --all-files
```

### Testing

It uses [pytest](https://docs.pytest.org/en/stable/) as the test framework. To run the tests:

```bash
poetry run pytest
```

To update the [syrupy](https://github.com/tophat/syrupy) snapshot tests:

```bash
poetry run pytest --snapshot-update
```

## License

MIT License

Copyright (c) 2022-2025 Klaas Schoute

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[api]: https://offenedaten-koeln.de
[disabled_parkings]: https://offenedaten-koeln.de/dataset/behindertenparkpl%C3%A4tze-k%C3%B6ln
[nipkaart]: https://www.nipkaart.nl

<!-- MARKDOWN LINKS & IMAGES -->
[build-shield]: https://github.com/klaasnicolaas/python-koeln/actions/workflows/tests.yaml/badge.svg
[build-url]: https://github.com/klaasnicolaas/python-koeln/actions/workflows/tests.yaml
[commits-shield]: https://img.shields.io/github/commit-activity/y/klaasnicolaas/python-koeln.svg
[commits-url]: https://github.com/klaasnicolaas/python-koeln/commits/main
[codecov-shield]: https://codecov.io/gh/klaasnicolaas/python-koeln/branch/main/graph/badge.svg?token=CRONIDYXGQ
[codecov-url]: https://codecov.io/gh/klaasnicolaas/python-koeln
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/klaasnicolaas/python-koeln
[downloads-shield]: https://img.shields.io/pypi/dm/koeln
[downloads-url]: https://pypistats.org/packages/koeln
[license-shield]: https://img.shields.io/github/license/klaasnicolaas/python-koeln.svg
[last-commit-shield]: https://img.shields.io/github/last-commit/klaasnicolaas/python-koeln.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2025.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-production%20ready-brightgreen.svg
[pypi]: https://pypi.org/project/koeln/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/koeln
[typing-shield]: https://github.com/klaasnicolaas/python-koeln/actions/workflows/typing.yaml/badge.svg
[typing-url]: https://github.com/klaasnicolaas/python-koeln/actions/workflows/typing.yaml
[releases-shield]: https://img.shields.io/github/release/klaasnicolaas/python-koeln.svg
[releases]: https://github.com/klaasnicolaas/python-koeln/releases

[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com
