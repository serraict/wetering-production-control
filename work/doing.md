# Doing

In this document we describe what we are working on now.

## Dremio Backup Command Implementation

### To Do

- [x] Created initial backup command module in `src/production_control/data/backup.py`
- [x] Add CLI integration in `src/production_control/__cli__.py`
- [x] Create test file `tests/cli/test_backup_commands.py`
- [x] Update documentation in `readme.md`
- [x] Review command line interface
- [x] Parameter defaults - are they properly set?
- [x] Check typer docs to learn if we use annotations correctly
- [x] Improve CLI interface
- [x] Rename command from `backup-table` to `query`
- [x] Add `--name` parameter for backup file naming
- [x] Add environment variable support for output directory
- [x] Create entry point for `pc` command in pyproject.toml
- [x] Add test for environment variable precedence
- [x] Update help text and documentation

### Detailed steps

1. ~~Modify backup command in backup.py:~~

   - ~~Rename command from `backup-table` to `query`~~
   - ~~Add `--name` parameter for backup file naming~~
   - ~~Add environment variable support for output directory~~
   - ~~Update help text and documentation~~

1. ~~Create entry point for `pc` command:~~

   - ~~Add script entry point in pyproject.toml~~
   - ~~This will allow using `pc` instead of `production_control`~~

1. ~~Update tests:~~

   - ~~Update test cases to use new command structure~~
   - ~~Add tests for name parameter~~
   - ~~Add test for environment variable precedence~~

1. Example of new interface:

   ```bash
   # Old interface
   production_control backup backup-table "SELECT * FROM table" --output-dir dir

   # New interface
   pc backup query "select * from bestelling where ar > 0" --name afroep_opdrachten
   ```

### Implementation Notes

- Using SQLAlchemy engine from repository pattern
- Chunking large result sets to manage memory
- CSV output with headers from result keys
- Error handling for both DB and filesystem operations
