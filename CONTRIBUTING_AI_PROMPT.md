# AI/LLM Contributing Guidelines for Production Control

This guide supplements CONTRIBUTING.md with specific guidelines for AI/LLM contributors.
Follow both this guide and the main CONTRIBUTING.md when making changes.

## Workflow

The currently active task is described in [doing.md](./work/doing.md).

Things we consider doing in the future are described in [backlog.md](./work/backlog.md).

## Tool Usage

1. Use tools step-by-step, one at a time:
   - Wait for user confirmation after each tool use
   - Base next steps on results of previous tool uses
   - Don't assume success without explicit confirmation

2. Choose appropriate tools:
   - Use `list_files` instead of `ls` commands
   - Use `search_files` for finding code patterns
   - Use `read_file` to examine specific files
   - Use `write_to_file` for all file modifications
   - Use `execute_command` for necessary CLI operations
   - Use `browser_action` for web interface tasks

3. When to ask questions:
   - Use `ask_followup_question` only when tools cannot provide needed information
   - Keep questions specific and focused
   - Prefer using available tools over asking questions

## Context Understanding

1. Always use `<thinking>` tags to explain your reasoning:
   - Analyze available information
   - Explain tool choice rationale
   - Document decision-making process

2. When working on adding new features, do not change infrastructural code like:
   - `src/web/components`
   - test infrastructure
   - shared base classes

3. Before making changes:
   - Analyze project structure:
     - `src/production_control/` - Main application code
     - `tests/` - Unit tests
     - `tests/web/` - Web interface tests
     - `tests/integration/` - Integration tests

   - Review related files:
     - Check similar files for patterns and conventions
     - Review test files to understand expected behavior
     - Look for project-specific idioms

4. Quality standards:
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

2. Documentation:
   - Update docstrings
   - Add inline comments for complex logic
   - Update CHANGELOG.md following Keep a Changelog format

3. Quality Checks:
   - Run `make test` to run tests
   - Run `make format` to format code and documentation
   - Run `make quality` for linting and formatting
   - Ensure all tests pass
   - Verify changes meet project standards

## Version Control

1. Do not commit and push with a single command.
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

## Environment Details

1. Always consider the environment details provided:
   - Check for actively running terminals
   - Note open files and visible files
   - Use current working directory information
   - Consider system information for commands

2. Handle sensitive information:
   - Do not read or expose .env files
   - Avoid exposing secrets or credentials
   - Use environment variables appropriately

## Task Completion

1. Use `attempt_completion` tool only when:
   - All previous tool uses are confirmed successful
   - The task is fully complete
   - No further user input is needed

2. Provide clear, final results:
   - Summarize changes made
   - Document any important considerations
   - Avoid ending with questions or offers for assistance
