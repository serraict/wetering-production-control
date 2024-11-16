# AI/LLM Contributing Guidelines for Production Control

This guide supplements CONTRIBUTING.md with specific guidelines for AI/LLM contributors.
Follow both this guide and the main CONTRIBUTING.md when making changes.

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

   - Run `make quality` for linting and formatting
   - Ensure all tests pass
   - Verify changes meet project standards

## Version Control

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
   - Reference related issues/PRs

## Quality Checklist

Before completing task:

1. Code Quality

   - [ ] Follows project structure and patterns
   - [ ] Includes appropriate type hints
   - [ ] Has necessary docstrings
   - [ ] Passes linting and formatting

1. Testing

   - [ ] Unit tests added/updated
   - [ ] Integration tests if needed
   - [ ] All tests pass
   - [ ] Test coverage maintained

1. Documentation

   - [ ] Code is self-documenting
   - [ ] Complex logic explained
   - [ ] CHANGELOG.md updated

1. Version Control

   - [ ] Changes are atomic
   - [ ] Commit messages follow convention
   - [ ] Changes are properly scoped


## Framework-Specific Guidelines

### NiceGUI Testing

When testing NiceGUI components:

1. Test File Organization:

   - Place web interface tests in `tests/web/`
   - Create separate test files for distinct features
   - Use descriptive test names that explain the behavior being tested
   - Follow the Given/When/Then pattern in test comments

1. Page Navigation and Content Verification:

   ```python
   # Navigate to a page
   await user.open("/some-route")

   # Verify visible text content
   await user.should_see("Expected Text")

   # Click links or buttons
   user.find("Link Text").click()
   ```

1. Table Testing:

   ```python
   # Get table component
   table = user.find(ui.table).elements.pop()

   # Verify table structure
   assert table.columns == [
       {"name": "col1", "label": "Column 1", "field": "field1"},
   ]

   # Verify table data
   assert table.rows == [
       {"field1": "value1"},
   ]
   ```

1. Form Testing:

   ```python
   # Input text
   await user.type("input text")

   # Select options
   await user.select("option label")

   # Submit forms
   await user.click("Submit")
   ```

1. Common Patterns:

   - Use `user.should_see()` for text content verification
   - Use `user.find()` for element interaction
   - Use `user.open()` for page navigation
   - Mock external dependencies (repositories, services)
   - Test both success and error scenarios

1. Best Practices:

   - Test one behavior per test function
   - Use clear, descriptive test names
   - Follow the project's existing test patterns
   - Keep assertions focused and minimal
   - Mock external dependencies consistently

Remember that NiceGUI's testing module provides specific ways to verify UI elements.
Don't try to access internal properties directly, but use the provided testing utilities.

### Exploratory Testing with Browser Actions

After implementing UI changes, perform exploratory testing using the browser_action tool:

1. Setup:

   - Start the development server in a separate terminal using `make server`
   - Keep the server terminal visible to monitor logs and errors
   - Use browser_action tools in the main terminal for testing

1. Testing Flow:

   ```python
   # Launch browser at specific URL
   <browser_action>
   <action>launch</action>
   <url>http://localhost:8080/your-page</url>
   </browser_action>

   # Interact with elements (after analyzing screenshot)
   <browser_action>
   <action>click</action>
   <coordinate>450,300</coordinate>
   </browser_action>

   # Always close browser when done
   <browser_action>
   <action>close</action>
   </browser_action>
   ```

1. Key Aspects to Test:

   - Visual appearance and layout
   - Interactive elements (buttons, links, forms)
   - Sorting and filtering functionality
   - Error states and edge cases
   - Responsive behavior
   - Console errors or warnings

1. Best Practices:

   - Always analyze screenshots after each action
   - Monitor console logs for errors
   - Test both happy path and edge cases
   - Close browser before using other tools
   - Document any issues found
   - Verify fixes with both automated tests and browser actions

Remember that browser actions complement automated tests by allowing manual verification of the user experience. Use both approaches to ensure comprehensive testing coverage.

