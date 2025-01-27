# Doing

In this document we describe what we are working on now.

## Dremio Backup Command Implementation

### Current Status

- [x] Created initial backup command module in `src/production_control/data/backup.py`
- [x] Add CLI integration in `src/production_control/__cli__.py`
- [x] Create test file `tests/cli/test_backup_commands.py`
- [x] Update documentation in `readme.md`

### Next Steps

1. Update `__cli__.py` to integrate backup command:
```python
from production_control.data import backup

app.add_typer(backup.app, name="backup", help="Dremio backup commands")
```
2. Create test file with cases:
   - Test successful backup
   - Test handling of invalid SQL
   - Test file system errors
   - Test chunking with large result sets
3. Add documentation to readme.md:
   - Command usage examples
   - Configuration options
   - Common use cases

### Implementation Notes

- Using SQLAlchemy engine from repository pattern
- Chunking large result sets to manage memory
- CSV output with headers from result keys
- Error handling for both DB and filesystem operations

### Questions

Typer: should we use annotations for parameters?
