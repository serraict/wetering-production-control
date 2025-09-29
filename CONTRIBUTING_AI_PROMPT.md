# AI/LLM Contributing Guidelines for Production Control

This guide supplements CONTRIBUTING.md with specific guidelines for AI/LLM contributors.
Follow both this guide and the main CONTRIBUTING.md when making changes.

## Test-First Development

1. Start with a single test:

   - Choose the simplest test case first
   - Focus on one piece of functionality
   - Write only one test before writing code
   - Get that test passing before writing the next

1. Keep the test-code cycle small:

   - Write minimal test code
   - Write minimal production code to pass
   - Refactor only after test passes
   - Move to next test only after current test is stable

1. Choose the first test wisely:

   - Start with basic existence/structure tests
   - Then add basic functionality tests
   - Progress to edge cases
   - End with error conditions

1. Example test progression:

   ```python
   # First test: verify component exists
   def test_component_exists():
       assert Component() is not None

   # Second test: verify basic functionality
   def test_component_basic_operation():
       assert Component().operation() == expected_result

   # Later test: verify edge case
   def test_component_handles_empty_input():
       assert Component().operation("") == default_value
   ```

   Do not add "#ARRANGE ... #ACT ... #ASSERT ..." or "#GIVEN ... #WHEN ... #THEN" comments.

## Workflow

The currently active task is described in [doing.md](./work/doing.md).

Things we consider doing in the future are described in [backlog.md](./work/backlog.md).

When a task is done, suggest a prompt to start the next task.

## Tool Usage

1. Use tools step-by-step, one at a time:

   - Wait for user confirmation after each tool use
   - Base next steps on results of previous tool uses
   - Don't assume success without explicit confirmation

1. Choose appropriate tools:

   - Use `list_files` instead of `ls` commands
   - Use `search_files` for finding code patterns
   - Use `read_file` to examine specific files
   - Use `write_to_file` for all file modifications
   - Use `execute_command` for necessary CLI operations
   - Use `browser_action` for web interface tasks
   - Use `./scripts/dremio_cli/dremio_query.py` to inspect the Dremio lakehouse

1. When to ask questions:

   - Use `ask_followup_question` only when tools cannot provide needed information
   - Keep questions specific and focused
   - Prefer using available tools over asking questions

## Context Understanding

1. Always use `<thinking>` tags to explain your reasoning:

   - Analyze available information
   - Explain tool choice rationale
   - Document decision-making process

1. When working on adding new features, do not change infrastructural code like:

   - `src/web/components`
   - test infrastructure
   - shared base classes

1. Before making changes:

   - Analyze project structure:

     - `src/production_control/` - Main application code
     - `tests/` - Unit tests
     - `tests/web/` - Web interface tests
     - `tests/integration/` - Integration tests

   - Review related files:

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

   - Write one failing test
   - Implement minimum code to pass that test
   - Refactor while keeping test green
   - Only then move to next test
   - Keep test code simple and readable

1. When tests fail:

   - Focus on one failing test at a time
   - Make minimal changes to pass the test
   - Verify fix doesn't break other tests
   - Document test fixes in commits

1. Documentation:

   - Update docstrings
   - Add inline comments for complex logic
   - Update CHANGELOG.md following Keep a Changelog format

1. Quality Checks:

   - Run `make test` to run tests
   - Run `make format` to format code and documentation
   - Run `make quality` for linting and formatting
   - Ensure all tests pass
   - Verify changes meet project standards

## Language and UI Guidelines

1. Follow language conventions:

   - Use Dutch for all user-facing text (UI labels, messages)
   - Use English for code, comments, and documentation
   - Follow existing patterns for terminology and phrasing
   - Check similar components for language consistency

1. UI Development:

   - Match existing UI patterns and structures
   - Follow component naming conventions
   - Maintain consistent styling
   - Test UI changes thoroughly

## Version Control

1. Do not commit and push with a single command.
   Commits should be done often, pushes when they make sense.

1. Make atomic commits representing single logical changes

1. Follow Conventional Commits format:

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

1. Commit messages should:

   - Clearly explain the change
   - Include context and reasoning

1. After pushing changes:

   - Monitor CI workflow status:

     ```shell
     python scripts/check_workflow.py CI --watch
     ```

   - Address any CI failures promptly

   - Make necessary fixes in new commits

## Environment Details

1. Always consider the environment details provided:

   - Check for actively running terminals
   - Note open files and visible files
   - Use current working directory information
   - Consider system information for commands

1. Handle sensitive information:

   - Do not read or expose .env files
   - Avoid exposing secrets or credentials
   - Use environment variables appropriately

## Task Completion

1. Use `attempt_completion` tool only when:

   - All previous tool uses are confirmed successful
   - The task is fully complete
   - No further user input is needed

1. Provide clear, final results:

   - Summarize changes made
   - Document any important considerations
   - Avoid ending with questions or offers for assistance

## Iterative Development

1. Break down complex changes:

   - Start with one test
   - Make small, focused changes
   - Build on successful tests
   - Keep changes reversible

1. Handle test failures:

   - Fix one failure at a time
   - Verify fixes don't introduce new failures
   - Consider test dependencies
   - Document test fixes in commits
