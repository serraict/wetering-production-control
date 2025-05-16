# Doing

# Completed

## Speed up label generation

Issue: UI blocks when downloading many labels (20+), connection drops, and labels can't be downloaded after reconnect.

### Solution: Move to Background Task

We implemented the following improvements:

1. Moved label generation to background tasks:

   - Used `run.cpu_bound` to process labels in a separate process
   - Added progress notifications
   - Kept UI responsive during generation
   - Added proper error handling

1. Enhanced user feedback:

   - Disabled buttons during processing
   - Changed button icon to show processing state
   - Added notifications for generation start and errors
   - Re-enabled buttons after completion

1. Fixed parameter handling:

   - Corrected filename parameter usage
   - Removed unused imports
   - Simplified code structure

Implementation details:

- Used NiceGUI's `run.cpu_bound` for CPU-intensive operations
- Added async handlers for both single and multi-label generation
- Implemented proper button state management
- Added comprehensive error handling

Applied to both:

- Potting lots page
- Bulb picklist page

### Future Improvements

If needed, we can further optimize the process by:

1. Profiling to identify specific bottlenecks
1. Implementing caching for frequently used labels
1. Optimizing QR code generation
1. Adding more detailed progress tracking

But the current implementation solves the immediate issue for our client by preventing UI blocking and connection drops.
