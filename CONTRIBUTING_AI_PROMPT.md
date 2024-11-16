# AI/LLM Contributing Guidelines for Production Control

This guide supplements CONTRIBUTING.md with specific guidelines for AI/LLM contributors.
Follow both this guide and the main CONTRIBUTING.md when making changes.

## Workflow

The currently active task is described in [doing.md](./work/doing.md).

Things we consider doing in the future is described in [backlog.md](./work/backlog.md).

## Context Understanding

Try to write tests to build your understanding of the context.

1. When working on adding new features, do not change infrastructural code like:

   - `src/web/components`

   - test infrastructure
   - shared base classes

Before making changes:

1. Analyze project structure:

   - `src/production_control/` - Main application code
   - `tests/` - Unit tests
   - `tests/web/` - Web interface tests
   - `tests/integration/` - Integration tests

1. Review related files:

   - Check similar files for patterns and conventions
   - Review test files to understand expected behavior
   - Look for project-specific idioms

1. Quality standards:

   - Use type hints for function parameters and return values
   - Include docstrings for modules, classes, and functions
   - Keep functions focused and under 20 lines
   - Keep cyclomatic complexity low (max 10)
   - Follow existing code style

## Making Changes

1. Test-Driven Development:

   - Write failing test first
   - Implement minimum code to pass
   - Refactor while keeping tests green
   - Keep test code simple and readable
   - Avoid unnecessary assertions

1. Documentation:

   - Update docstrings
   - Add inline comments for complex logic
   - Update CHANGELOG.md following Keep a Changelog format

1. Quality Checks:

   - Run `make test` to run test
   - Run `make format` to format code and documentation
   - Run `make quality` for linting and formatting
   - Ensure all tests pass
   - Verify changes meet project standards

## Version Control

1. Do not commit and push at with a single command.
   Commits should be done often, pushes when they make sense.

2. Make atomic commits representing single logical changes

3. Follow Conventional Commits format:

   ```text
   <type>[optional scope]: <description>
   ```

   Types:

   - feat: New feature
   - fix: Bug fix
   - docs: Documentation
   - style: Code style
   - refactor: Code restructuring
   - test: Test changes
   - chore: Build/tool changes

4. Commit messages should:

   - Clearly explain the change
   - Include context and reasoning
   - Reference related issues/PRs
