# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.61] - 2025-10-08

### Added

- Firebird database integration for persisting inspection changes:
  - Direct database writes eliminate manual re-entry into desktop application
  - FastAPI endpoints for updating afwijking values in Firebird database
  - "Opslaan in database" button in inspection page to commit pending changes
  - Parameterized SQL queries to prevent SQL injection vulnerabilities
  - Comprehensive test coverage for all Firebird integration code
  - Production-ready connection using fdb library with Firebird client libraries
  - Environment-based configuration for flexible deployment

### Changed

- Updated Dockerfile.base to include Firebird client libraries (libfbclient2)
- Inspection page now uses NICEGUI_PORT environment variable for API calls

## [0.1.36] - 2025-05-16

### Changed

- Significantly improved label generation performance:
  - Replaced div/flexbox layout with table-based layout in templates
  - Updated label styles for better WeasyPrint compatibility
  - Maintained visual appearance and QR code functionality
  - Achieved ~90% performance improvement for large batches (50+ labels)
  - Preserved template inheritance pattern for maintainability

### Documentation

- Updated architecture documentation

## [0.1.34] - 2025-05-15

### Changed

- Updated label layouts with new design requirements:
  - Set grid rows to 50/30/20 (top/middle/bottom)
  - Updated default label size to 104x77mm (from 151x101mm)
  - Set QR code to 30% width
  - Removed URL text from templates
  - Added cert_nr field to PottingLot model
  - Updated potting lot label template to show bolmaat and cert_nr

## [0.1.33] - 2025-05-15

### Added

- Added multiple pallet label generation for bulb picklist:
  - Calculate number of pallets based on box count (25 boxes per pallet)
  - Generate separate label for each pallet with "Pallet X/Y" indicator
  - Added comprehensive test coverage for pallet calculation and label generation

## [0.1.14] - 2025-05-13

### Changed

- Optimized Dockerfile with multi-stage builds:
  - Separated dependencies installation from code copying
  - Improved layer caching for faster deployments
  - Reduced build time when only Python code changes
  - Maintained full rebuild capability when dependencies change

## [0.1.13] - 2025-05-13

### Added

- Added new fields to PottingLot model:
  - Added product_groep field for product group information
  - Added klant_code field for customer code information
  - Added oppot_week field for potting week information
  - Added all new fields to search functionality
- Added duplicate label printing for potting lots:
  - Each potting lot now prints two identical labels (for start and end of lot)
  - Updated UI tooltips to indicate dual label printing
  - Added comprehensive test coverage for duplicate label generation

### Changed

- Improved label generation performance and code quality

## [0.1.11] - 2025-05-08

### Added

- Added multi-label printing for bulb lots:

  - Added Jinja2 for template rendering
  - Implemented batch label generation for next week's bulb lots
  - Added UI button for printing next week's labels

- Added Dremio backup command:

  - Export query results to CSV files with custom naming
  - Support for large result sets with chunking
  - Environment variable support for backup directory
  - Convenient `pc` command alias for shorter CLI usage

- Added warning filter to spacing page:

- Added Dremio CLI access:

  - Created Python script for executing SQL queries against Dremio
  - Added shell alias for easier access
  - Documented usage in CONTRIBUTING.md

- Added Bulb Picklist module:

  - Created BulbPickList model with proper field mappings
  - Implemented repository for data access with pagination and filtering
  - Added web interface for viewing bulb picklist data
  - Updated model to use id field as primary key instead of bollen_code
  - Added label generation functionality with PDF output
  - Implemented QR code generation with Serra logo
  - Added scan landing page for QR code links
  - Added potted week field (oppot_week) to bulb picking with search functionality and label display

### Changed

- Improved test quality:
  - Removed ORM mapping tests from models (focusing on behavior, not implementation details)
- Enhanced test coverage for date formatting utilities
- Updated spacing page tests to properly handle ISO week dates

### Fixed

- Fixed week number display for year-end dates (e.g., 2024-12-30 now correctly shows as 25w01-1)
- Improved date formatting consistency by moving it to server-side

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
