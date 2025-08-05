## Brief overview

This style guide defines the coding standards, organization patterns, and commenting philosophy for the Argus project. These guidelines ensure consistency across Python files and shell scripts, emphasizing minimal commenting, clear organization, and self-documenting code.

## File organization structure

- Use consistent section dividers: `# ============================================================================`
- Organize all files with the same structure:
  1. Header section (imports/variables/configuration)
  2. Utility functions
  3. Core business logic
  4. Main execution logic
- Apply section headers with descriptive ALL CAPS titles
- Group related functions under appropriate sections

## Minimal commenting philosophy

- Use function-level documentation only (docstrings for Python, brief comments for shell)
- Avoid inline comments unless explaining complex logic
- Make code self-documenting through clear naming conventions
- Remove explanatory comments that restate what the code does
- Example: Remove `# Get row count` before `row_count = con.execute(...)`

## Naming conventions

- Python: `snake_case` for functions and variables, `UPPER_CASE` for constants
- Shell: `UPPER_CASE` for script-level variables, `snake_case` for function names
- Use descriptive names that eliminate need for comments
- Functions should clearly indicate their purpose through naming

## Function documentation

- Python: Use triple-quote docstrings with brief purpose description
- Shell: Add single-line comment describing function purpose
- Format: `# Brief description of function purpose`
- Keep documentation concise and focused on what, not how

## Visual consistency

- Apply decorative section dividers to all files for visual organization
- Use consistent spacing and indentation (4 spaces for Python)
- Maintain uniform logging function usage across languages
- Keep consistent color schemes and message formats

## Error handling patterns

- Use consistent logging functions: `log_info()`, `log_success()`, `log_warning()`, `log_error()`
- Apply same exit codes and error propagation patterns
- Maintain uniform error message formatting across Python and shell scripts

## Code maintenance approach

- Prioritize readability over brevity
- Ensure changes maintain consistency across all project files
- Apply style changes systematically to all relevant files
- Review for consistency when adding new functions or sections