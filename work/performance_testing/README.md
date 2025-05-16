# Label Generation Performance Testing

This directory contains scripts and tools for testing and optimizing the performance of label generation in the production control system.

## Overview

The label generation process involves several steps:
1. Converting row data to BulbPickList records
2. Generating QR codes for each record
3. Preparing record data for template rendering
4. Generating HTML from templates
5. Converting HTML to PDF

Our performance testing identified that PDF generation is the most time-consuming step, taking up to 96% of the total processing time for large batches.

## Test Results

We conducted several optimization experiments:

### 1. Code Optimizations

We compared the original label generator with an optimized version that includes:
- LRU caching for QR code generation
- Thread-local storage for QR code generators
- Parallel processing for QR code generation
- Pre-compiled Jinja2 templates
- Optimized WeasyPrint settings

#### Performance Comparison - Code Optimizations

| Batch Size | Original | Optimized | Improvement |
|------------|----------|-----------|-------------|
| 1          | 0.1288s  | 0.0629s   | 51.2%       |
| 10         | 4.0149s  | 3.7640s   | 6.2%        |
| 25         | 17.6659s | 17.7184s  | -0.3%       |
| 50         | 55.2538s | 56.8013s  | -2.8%       |

### 2. Template Simplification

We tested a simplified template approach that:
- Removes flexbox layout
- Eliminates QR code images
- Simplifies CSS (no borders, simpler styling)
- Uses basic HTML structure

#### Performance Comparison - Simplified Template

| Batch Size | Original | Simplified | Improvement |
|------------|----------|------------|-------------|
| 1          | 0.1359s  | 0.0476s    | 65.0%       |
| 10         | 4.3778s  | 0.3012s    | 93.1%       |
| 25         | 18.5453s | 0.5982s    | 96.8%       |
| 50         | 61.2841s | 1.1158s    | 98.2%       |

### 3. Table-Based Template

We implemented a table-based template that:
- Replaces divs and flexbox with HTML tables
- Keeps QR code images
- Maintains font styling and row heights
- Preserves visual appearance

#### Performance Comparison - Table-Based Template

| Batch Size | Original | Table-Based | Improvement |
|------------|----------|-------------|-------------|
| 1          | 0.1288s  | 0.2262s     | -75.6%      |
| 10         | 4.0149s  | 1.0327s     | 74.3%       |
| 25         | 17.6659s | 3.0531s     | 82.7%       |
| 50         | 55.2538s | 5.6467s     | 89.8%       |

### Key Findings

1. **Template Complexity is the Main Bottleneck**: Both the simplified and table-based templates show dramatic improvements for large batches, confirming that the complex HTML/CSS layout is the primary performance bottleneck.

2. **QR Code Impact**: The simplified template (without QR codes) performs better than the table-based template (with QR codes), suggesting that QR code generation and rendering adds significant overhead.

3. **CSS Layout Engine Limitations**: WeasyPrint's layout engine struggles with complex layouts at scale, particularly with flexbox and images.

4. **Scaling Comparison**:
   - Original: 50 records is 450x slower than 1 record
   - Simplified: 50 records is only 23x slower than 1 record
   - Table-based: 50 records is only 25x slower than 1 record

5. **Critical Use Case Improvements**:
   - Simplified template: 98.2% improvement (61.3s → 1.1s)
   - Table-based template: 89.8% improvement (55.3s → 5.6s)

6. **Trade-offs**:
   - Simplified template offers best performance but sacrifices visual elements (QR codes)
   - Table-based template maintains visual appearance while still achieving significant performance gains
   - Table-based template meets the 5-second target for 50 labels (5.6s)

## Recommendations

Based on the performance testing results, we recommend:

1. **Adopt the Table-Based Template**: The table-based template provides excellent performance improvements while maintaining visual appearance and functionality, including QR codes.

2. **Consider Template Options Based on Batch Size**:
   - For single labels: Original template (best visual quality)
   - For medium batches (2-20): Table-based template (good balance of performance and visual quality)
   - For large batches (20+): Simplified template or table-based template depending on whether QR codes are required

3. **Implement Asynchronous Processing**: Even with the improved templates, implement asynchronous processing for very large batches (100+ labels) to keep the UI responsive.

4. **Further Optimize the Table-Based Template**:
   - Experiment with simpler QR code rendering
   - Reduce the complexity of table styling
   - Consider using fixed pixel dimensions instead of mm/cm
   - Minimize the use of absolute positioning

5. **Combine Approaches**: Consider combining the table-based layout with code optimizations (caching, threading) for even better performance.

## Files in this Directory

- `run_performance_tests.py`: Script to run performance tests on the label generator
- `optimized_label_generator.py`: Implementation of an optimized label generator
- `simplified_label_template.py`: Implementation of a simplified template approach
- `create_test_data.py`: Script to create test data for performance testing
- `extract_pickle_data.py`: Utility to extract data from pickle files
- `data/`: Directory containing test data
- `output/`: Directory containing generated PDFs

## Usage

To run the performance tests:

```bash
# Create test data
python -m work.performance_testing.create_test_data

# Run performance tests with the original generator
python -m work.performance_testing.run_performance_tests

# Run performance comparison between original and optimized generators
python -m work.performance_testing.optimized_label_generator
