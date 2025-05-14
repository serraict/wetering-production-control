# Doing

## Optimize Dockerfile with uv Package Manager and Multi-stage Builds

Rebuilding the Dockerfile from scratch to leverage uv package manager for improved dependency management and build performance. This approach aims to create a more efficient and maintainable Docker build process.

### Planned Changes

1. Create a new three-stage Dockerfile:
   - **Base stage**: System dependencies and uv installation
   - **Builder stage**: Dependencies installation and virtual environment setup
   - **Final stage**: Production runtime with minimal footprint

2. Key improvements:
   - Proper uv installation and configuration
   - Separate handling of dev vs prod dependencies
   - Optimized layer caching
   - Reduced image size by excluding dev tools in final stage
   - Proper environment variable handling

3. Implementation steps:
   a. Base stage:
      - Use Python 3.12-slim
      - Install minimal system dependencies
      - Install uv properly using official installation method
      
   b. Builder stage:
      - Install build dependencies
      - Create virtual environment with uv
      - Install production dependencies first
      - Install dev dependencies separately
      - Build wheel of our application
      
   c. Final stage:
      - Copy only necessary files from builder
      - Install runtime system dependencies
      - Install application wheel
      - Set up logging and entrypoint

### Expected Benefits
- More efficient dependency management with uv
- Cleaner separation of build stages
- Improved caching for faster builds
- Smaller final image size
- Better maintainability

### Implemented Changes

1. Fixed WeasyPrint dependency issue:
   - Added required system libraries for WeasyPrint in the base stage:
     - libcairo2
     - libpango-1.0-0
     - libpangocairo-1.0-0
     - libgdk-pixbuf2.0-0
     - libffi-dev
     - shared-mime-info
     - libgirepository1.0-dev
     - libglib2.0-0

2. Optimized Docker layer structure:
   - Moved all system dependencies and runtime tools to the base stage
   - Changed production stage to inherit from base instead of python:3.12-slim-bookworm
   - Removed all duplicate system dependency installation from production stage
   - Production stage now has no apt-get commands, inheriting everything from base

### Next Steps
1. Test build process and verify improvements
2. Update documentation with new build process details
3. Verify all tests pass with new container
4. Monitor build times and image sizes to confirm optimization
