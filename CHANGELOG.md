# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2024-11-21

### Added

- Spacing module with comprehensive features:
  - Table view of spacing records with Dutch labels
  - Search, pagination, and sorting functionality
  - Error visualization for problematic records
  - Record correction interface with OpTech integration
  - Command-line interface for spacing operations

### Changed

- Refactored table components:
  - Enhanced models with UI metadata
  - Created model-driven table column generator
  - Implemented ServerSidePaginatingTable component
  - Added Dutch labels throughout the interface
  - Improved table state management per client connection
- Refactored repositories:
  - Made DremioRepository generic with model type T
  - Moved common functionality to base class
  - Improved session handling

### Added

- Data formatting utilities:
  - Date formatting
  - Decimal formatting
  - Support for custom field formatting

## [0.1.2] - 2024-11-18

### Added

- First successful production deployment
- Enhanced AI/LLM contributing guidelines with comprehensive instructions
- Completed template review with improvement recommendations

### Changed

- Updated contributing guidelines with clearer instructions
- Expanded template review with insights from project history

### Fixed

- Fixed database connection issue causing 500 error on products page

## [0.1.0] - 2024-11-16

### Added

- Initial project setup with cookiecutter template

- Basic project structure with Python package configuration

- Development tooling and quality checks

  - Black code formatting
  - Flake8 linting
  - MDFormat for markdown files
  - Pytest for testing
  - Coverage reporting

- Docker support with development environment

- Make commands for common development tasks

- Web interface using NiceGUI

- Command-line interface using Typer

- Dremio integration for data access

- Products module with repository pattern

- First release of the project
