# Contributing to Production Control

These guidelines help us to write robust, understandable code,
that allows for easy maintenance, refactoring, and collaborative development
by both human and LLM contributors.

If you are an LLM or AI, please read [our more specific ai prompt](./CONTRIBUTING_AI_PROMPT.md) too,
especially the Test-First Development section which provides detailed guidance
on our single-test-at-a-time approach.

## Definition of Done

Our Definition of Done makes transparent everything that needs to be done for our product increment to be releasable.
Our product increment is deemed releasable if `make release` would result in a published package
of the required quality standard
that we confidently install at a customer.

This means that:

- The work identified in [doing](./work/doing.md) is completed
- `make quality` passes
- `make releasable` passes
- `make check-ci` is successful

### Coding guidelines

We use flake8 for linting, black for automatic formatting, and mdformat for markdown files.

```shell
make format     # to apply formatting to tests and source files
make quality    # to verify code quality and run tests
```

### Versioning

We follow [Semantic Versioning](https://semver.org/) (SemVer) for version numbers.
The project version is determined using `setuptools_scm`.

### Language Guidelines

For user-facing text in the web interface (UI labels, messages, etc.), use Dutch language.
Follow existing patterns in the codebase for terminology and phrasing.
Code, comments, and documentation should be in English.

### Changelog

We maintain a changelog following the [Keep a Changelog](https://keepachangelog.com/) format.
Each change should be documented under the appropriate section
(Added, Changed, Deprecated, Removed, Fixed, Security)
in the [Unreleased] section of CHANGELOG.md.

## Way of Working

Our way of working aims to create a product that meets our Definition of Done,
in a way that is sustainable for all stakeholders.

### Collaboration

We behave kindly, think critically, and act deliberately.

### Commit Guidelines

Make atomic commits that represent a single, logical change.
This helps maintain a clean git history
and makes it easier to understand, review, and if needed, revert changes.

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages.

### Test Driven Development

We prefer to write tests before production code.
Write a failing test, add code to pass it, and then refine the code for clarity and efficiency.

### Testing

Unit tests are placed in the `./tests/` directory.
We record the coverage of our unit tests.
Our test coverage should not drop between commits.

### Development Environment

1. Create and activate a virtual environment:

```shell
make bootstrap
source .venv/bin/activate
```

2. Install dependencies and development tools:

```shell
make update
```

3. Run tests to verify setup:

```shell
make test
```

4. Start the development server:

```shell
make server
```

The project uses [uv](https://docs.astral.sh/uv/) for fast dependency management.
Development dependencies are defined in `pyproject.toml` under `[project.optional-dependencies]` and automatically installed with `make update`.

### Dremio CLI Access

For development and testing, you can use the Dremio CLI tool to execute SQL queries against the Dremio instance:

```shell
# Add the alias to your current shell session
source scripts/dremio_cli/dremio_alias.sh

# Execute a simple query
dremio-query "SELECT * FROM table"

# Execute a query from a file
dremio-query --file path/to/query.sql
```

See the [Dremio CLI README](./scripts/dremio_cli/README.md) for more details on usage and example queries.

### Docker Development

1. Build and start services:

```shell
make docker_compose_debug
```

2. Build Docker image:

```shell
make docker_image
```

### Releasing

Releases are created using a Github action.

To release:

1. Commit any pending changes and push to origin
1. Run:

```shell
make release
```

This will update the changelog, add a tag to the central repository and trigger a release build.
