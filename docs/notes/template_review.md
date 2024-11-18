# Template review

Here we list our experiences using the cookiecutter-vine-app template.
These notes will be used to improve the template for future projects.

## Experiences

venvg was ignored intead of venv

.python-version was missing, so wrong venv was created. Maybe do an assertion in the make bootstrap file

scripts directory was missing

## Advice

In general, do a git log on the template files to see what has changed and why.

### Start

Consider adding some form of work organization to get started.
I used the work directory.

Have Claude create its own commits, signed of by the navigator.

make bootstrap should create .python-version and .env

### More

1. Project Organization:

   - Add a `work/` directory by default with:
     - doing.md for active work tracking
     - backlog.md for future work
   - Add a `scripts/` directory for utility scripts
   - Include template for system architecture documentation

1. Development Setup:

   - Add assertions in bootstrap to verify correct Python version
   - Include .env.example with required variables
   - Add setuptools_scm for version management from start
   - Include basic makefile targets for common tasks

1. Documentation:

   - Include template for CHANGELOG.md following Keep a Changelog
   - Add template for architecture/vision documentation
   - Include AI/LLM specific contributing guidelines
   - Add template review document from start

1. CI/CD:

   - Include GitHub Actions workflows for:
     - CI (tests, quality checks)
     - Package building (Docker)
   - Add workflow monitoring utilities
   - Include Codecov integration setup

### Keep

1. Basic Structure:

   - Python package setup with tests
   - Docker support
   - Quality tools (black, flake8)
   - Make-based workflow

1. Documentation:

   - Contributing guidelines
   - README structure
   - License handling

### Less

1. Simplify initial setup:
   - Reduce number of manual post-template steps
   - Automate more of the initial configuration

### Stop

1. Wrong defaults:

   - Using incorrect venv name in .gitignore
   - Missing critical files (.python-version, .env)
   - Missing useful directories (scripts/, work/)

1. Manual steps that could be automated:

   - Version management setup
   - Initial documentation structure
   - Basic CI/CD configuration
