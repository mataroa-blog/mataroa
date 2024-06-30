# Dependencies

## Dependency Policy

The mataroa project has an unusually strict yet usually unclear dependency policy.

Vague rules include:

* No third-party Django apps.
* All Python / PyPI packages should be individually vetted.
    * Packages should be published from community-trusted organisations or developers.
    * Packages should be actively maintained (though not necessarily actively developed).
    * Packages should hold a high quality of coding practices.
* No JavaScript libraries / dependencies.

Current list of top-level PyPI dependencies (source at [requirements.in](/requirements.in)):

* [Django](https://pypi.org/project/Django/)
* [psycopg2-binary](https://pypi.org/project/psycopg2-binary/)
* [uWSGI](https://pypi.org/project/uWSGI/)
* [Markdown](https://pypi.org/project/Markdown/)
* [Pygments](https://pypi.org/project/Pygments/)
* [bleach](https://pypi.org/project/bleach/)
* [stripe](https://pypi.org/project/stripe/)

## Adding a new dependency

After approving a dependency, the process to add it is:

1. Assuming a venv is activated and `requirements_dev.txt` are installed.
1. Add new dependency in [`requirements.in`](/requirements.in).
1. Run `pip-compile` to generate [`requirements.txt`](/requirements.txt)
1. Run `pip install -r requirements.txt`

## Upgrading dependencies

When a new Django version is out it’s a good idea to upgrade everything.

Steps:

1. Assuming a venv is activated and `requirements_dev.txt` are installed.
1. Run `pip-compile -U` to generate an upgraded `requirements.txt`.
1. Run `git diff requirements.txt` and spot non-patch level vesion bumps.
1. Examine release notes of each one.
1. Unless something comes up, make sure tests and smoke tests pass.
1. Deploy new dependency versions.
