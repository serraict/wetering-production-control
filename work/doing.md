# Doing


# Completed

## Speed up label generation

We conducted a comprehensive performance analysis of the label generation process:

### Performance Testing Setup
1. Created test dataset with 50 records and varying pallet counts
2. Implemented performance testing scripts with timing decorators
3. Tested batch sizes of 1, 10, 25, and 50 records
4. Measured time for each component: QR code generation, data preparation, HTML rendering, and PDF generation

### Key Findings
1. PDF generation is the primary bottleneck (96% of total time for large batches)
2. Processing time increases non-linearly with batch size:
   - Batch size 1: ~0.13s
   - Batch size 10: ~4.0s (31x slower than single batch)
   - Batch size 25: ~17.7s (136x slower than single batch)
   - Batch size 50: ~55.3s (425x slower than single batch)
3. WeasyPrint's layout engine complexity increases with document size
4. Optimizations helped for small batches but not for the critical 25-50 record use case

### Implemented Optimizations

#### 1. Code Optimizations
- LRU caching for QR code generation
- Thread-local storage for QR code generators
- Parallel processing for QR code generation
- Pre-compiled Jinja2 templates
- Optimized WeasyPrint settings

**Results:**
| Batch Size | Original | Optimized | Improvement |
|------------|----------|-----------|-------------|
| 1          | 0.1288s  | 0.0629s   | 51.2%       |
| 10         | 4.0149s  | 3.7640s   | 6.2%        |
| 25         | 17.6659s | 17.7184s  | -0.3%       |
| 50         | 55.2538s | 56.8013s  | -2.8%       |

#### 2. Template Simplification
- Removed flexbox layout
- Eliminated QR code images
- Simplified CSS (no borders, simpler styling)
- Used basic HTML structure

**Results:**
| Batch Size | Original | Simplified | Improvement |
|------------|----------|------------|-------------|
| 1          | 0.1359s  | 0.0476s    | 65.0%       |
| 10         | 4.3778s  | 0.3012s    | 93.1%       |
| 25         | 18.5453s | 0.5982s    | 96.8%       |
| 50         | 61.2841s | 1.1158s    | 98.2%       |

### Key Findings
1. Template complexity is the main bottleneck, not code efficiency
2. WeasyPrint's layout engine struggles with complex layouts at scale
3. Simplified template approach reduces processing time from ~60s to ~1s for 50 records
4. QR codes and flexbox layouts significantly impact rendering performance

### Recommendations
1. Implement a two-template strategy:
   - Current template for single labels (visual quality)
   - Simplified template for batch printing (performance)
2. Consider making QR codes optional for batch printing
3. Replace flexbox with simpler layout techniques
4. Minimize nested elements and complex CSS
5. Implement asynchronous processing for very large batches

### Documentation
- Created detailed README.md in work/performance_testing/
- Documented all scripts and findings
- Provided recommendations for future improvements

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

### Notes

Code to save tables tate:

```Python
# Save table state for performance testing
import pickle
from pathlib import Path

# Create output directory if it doesn't exist
output_dir = Path("work/performance_testing/data")
output_dir.mkdir(parents=True, exist_ok=True)

# Save table state to pickle file
output_path = output_dir / "bulb_picklist_table_state.pkl"
with open(output_path, "wb") as f:
   pickle.dump(table_state.rows, f)

# Show notification
ui.notify(f"Saved table state with {len(table_state.rows)} rows to {output_path}")
```
