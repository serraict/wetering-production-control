# Doing

## Speed up label generation

Current issue: UI blocks when downloading many labels (20+), connection drops, and labels can't be downloaded after reconnect.

### Phase 1: Move to Background Task

1. Update potting lots page to use background task:
   - Move entire label generation process to a CPU-bound background task
   - Add progress notification
   - Keep UI responsive
   - Handle errors gracefully

Implementation in `src/production_control/web/pages/potting_lots.py`:

```python
def generate_labels(records, filename) -> str:
    """Generate PDF labels for records in a background process.
    
    Args:
        records: List of PottingLot records
        filename: Name for the output file
        
    Returns:
        Path to the generated PDF file
    """
    label_generator = LabelGenerator()
    return label_generator.generate_pdf(records, filename)

async def handle_print_all():
    table_state = ClientStorageTableState.initialize(table_state_key)
    records = [PottingLot(**visible_row) for visible_row in table_state.rows]
    
    if not records:
        return
        
    ui.notify('Generating labels...')
    
    try:
        # Generate labels in background process
        filename = f"oppotpartijen_{date.today():%gW%V-%u}.pdf"
        pdf_path = await run.cpu_bound(generate_labels, records, filename)
        
        # Download and cleanup
        ui.download(pdf_path)
        label_generator.cleanup_pdf(pdf_path)
        
    except Exception as e:
        ui.notify(f'Error generating labels: {str(e)}', type='error')
```

Success Criteria:
1. UI remains responsive during label generation
2. No connection drops
3. Clear progress indication
4. Graceful error handling

Implementation Steps:
1. Update potting lots page with background task implementation
2. Test with various batch sizes
3. Verify UI responsiveness
4. Test error scenarios

Git Commits:
```bash
git add src/production_control/web/pages/potting_lots.py
git commit -m "Move label generation to background task to prevent UI blocking"
```

### Next Steps

After this is working well for the client, we can:
1. Gather usage data and feedback
2. Profile the process if needed
3. Implement targeted optimizations based on actual bottlenecks

But first, let's get the background task working to solve the immediate issue for our client.
