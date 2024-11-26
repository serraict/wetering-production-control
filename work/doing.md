# Doing

In this document we describe what we are working on now.

## Goal: User can track spacing process segment

- Create functionality to record spacing operations (new and historical)
- Enable correction of ~200 lots with incorrect spacing data from January 2023
- Must be completed this week
- Critical for accurate cost determination per lot
- Impacts greenhouse space utilization tracking

### Completed

- Created data model and repository for spacing records with SQLModel
- Built web interface for viewing and correcting spacing records
- Implemented OpTech API integration for applying corrections
- Batch fix lots through the command line
- Added CLI functionality:
  - List and filter spacing errors
  - Preview corrections with dry-run support
  - Apply corrections with validation
  - Proper logging and error handling
  - Comprehensive test coverage
