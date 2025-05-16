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

We also tested a simplified template approach that:
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

### Key Findings

1. **Template Complexity is the Main Bottleneck**: The simplified template approach shows dramatic improvements (up to 98.2% for large batches), confirming that the complex HTML/CSS layout is the primary performance bottleneck.

2. **QR Code Generation**: While our code optimizations improved QR code generation, this is a minor factor compared to the template complexity.

3. **CSS Layout Engine Limitations**: WeasyPrint's layout engine (which is based on browser rendering engines) struggles with complex layouts at scale, particularly with flexbox and images.

4. **Linear Scaling with Simplified Template**: With the simplified template, processing time scales much more linearly with batch size:
   - Original: 50 records is 450x slower than 1 record
   - Simplified: 50 records is only 23x slower than 1 record

5. **Critical Use Case Dramatically Improved**: For the most important use case (25-50 records), the simplified template approach reduces processing time from ~60 seconds to ~1 second, a 98% improvement.

## Recommendations

Based on the performance testing results, we recommend:

1. **Implement the Simplified Template Approach**: The simplified template approach provides dramatic performance improvements for all batch sizes, especially for the critical 25-50 record use case.

2. **Two-Template Strategy**:
   - Use the current template for single-label printing where visual quality is most important
   - Use the simplified template for batch printing (10+ labels) where performance is critical

3. **Maintain Visual Consistency**: While simplifying the template, maintain essential information and visual hierarchy to ensure labels remain functional and recognizable.

4. **Consider Removing QR Codes for Batch Printing**: QR codes add significant complexity to the rendering process. Consider making them optional for batch printing or generating them separately.

5. **Implement Asynchronous Processing**: Even with the simplified template, implement asynchronous processing for very large batches (100+ labels) to keep the UI responsive.

6. **Optimize CSS Further**: If visual design is critical, explore targeted CSS optimizations:
   - Replace flexbox with simpler layout techniques
   - Minimize nested elements
   - Reduce the use of borders and complex styling
   - Use simpler units (px instead of mm/cm)

## Files in this Directory

- `run_performance_tests.py`: Script to run performance tests on the original label generator
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
