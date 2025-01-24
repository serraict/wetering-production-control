# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added warning filter to spacing page:
  - Toggle to show only records with warning messages
  - Integrated with existing search and pagination
  - Enhanced repository to support warning filtering
  - Added tests for warning filter functionality

### Fixed

- Fixed week number display for year-end dates (e.g., 2024-12-30 now correctly shows as 25w01-1)
- Improved date formatting consistency by moving it to server-side

### Changed

- Enhanced test coverage for date formatting utilities
- Updated spacing page tests to properly handle ISO week dates

## [0.1.5] - 2024-11-26

### Added

- Enhanced CLI functionality for spacing corrections:
  - Added `correct-spacing` command with dry-run support
  - Added validation for table counts and wdz1/wdz2 relationship
  - Added comprehensive error handling and user feedback
  - Added logging configuration for CLI operations

### Changed

- Enhanced SpacingRepository:
  - Added `get_by_partij_code` method while maintaining backward compatibility
  - Improved error handling for record lookups

## [0.1.4] - 2024-11-22

### Added

- Enhanced OpTech API integration:
  - Implemented OpTech API client with comprehensive error handling
  - Added timeout configuration for API calls
  - Improved error visualization in UI

### Changed

- Improved spacing table UI:
  - Updated column names for better clarity
  - Reordered fields to match business workflow
  - Enhanced error display in the interface

### Fixed

- Increased OpTech API timeout to handle slower responses
- Fixed field name mapping for OpTech API integration
- Improved error handling and display for API interactions

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
