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

Current list of top-level PyPI dependencies (source at [`pyproject.toml`](/pyproject.toml)):

* [Django](https://pypi.org/project/Django/)
* [psycopg](https://pypi.org/project/psycopg/)
* [gunicorn](https://pypi.org/project/gunicorn/)
* [Markdown](https://pypi.org/project/Markdown/)
* [Pygments](https://pypi.org/project/Pygments/)
* [bleach](https://pypi.org/project/bleach/)
* [stripe](https://pypi.org/project/stripe/)

## Adding a new dependency

After approving a dependency, add it using `uv`:

1. Ensure `uv` is installed and a virtualenv exists (managed by `uv`).
1. Add the dependency to `pyproject.toml` and lockfile with:
   - Runtime: `uv add PACKAGE`
   - Dev-only: `uv add --dev PACKAGE`
1. Install/sync dependencies: `uv sync`

## Upgrading dependencies

When a new Django version is out it’s a good idea to upgrade everything.

Steps:

1. Update the lockfile: `uv lock --upgrade`
1. Review changes: `git diff uv.lock` and spot non-patch level version bumps.
1. Examine release notes of each one.
1. Install updated deps: `uv sync`
1. Unless something comes up, make sure tests and smoke tests pass.
1. Deploy new dependency versions.
