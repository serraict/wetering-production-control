# Doing

## Optimize Dockerfile with uv Package Manager and Multi-stage Builds (COMPLETED)

### Current Issue
When pulling the Docker image after minor code changes, multiple layers need to be downloaded despite only application code changing. This is inefficient as theoretically only the final layers should need updating.

### Root Cause
The current setup doesn't properly leverage Docker's layer caching mechanism. While our Dockerfile has multiple stages (base, builder, production), we're not building and pushing these stages separately, causing unnecessary layer downloads.

### Implementation Summary

1. **Simplified Dockerfile Structure**
   - Reduced from three stages (base, builder, production) to two stages (base, app)
   - Moved dependencies to the base stage
   - Used fixed version for base stage to ensure caching works
   - Ensured version format is PEP 440 compliant (0.1.0.dev0)

2. **Updated Build Process**
   - Added docker_base target to build just the base image
   - Updated docker_image target to use base image for caching
   - Added docker_push_base and docker_push_all targets
   - Fixed version handling in build args

3. **Updated docker-compose.yml**
   - Added target specification for app stage
   - Added cache_from configuration to use base image
   - Added version argument handling

4. **Updated GitHub Actions Workflow**
   - Added step to build and push base image first
   - Updated app image build to use base image for caching
   - Fixed image naming and tagging
   - Ensured proper version handling

### Expected Outcome
- Faster deployments when only code changes
- Reduced bandwidth usage during pulls
- Better build caching
- Proper version management
- Streamlined CI/CD process

### Success Criteria
- Only final stage layers should be pulled when code changes
- Base and builder layers should remain cached
- Build time should be significantly reduced
- Version information should be correctly embedded

### Testing
To test the optimization:
1. Build the base image: `make docker_base`
2. Build the app image: `make docker_image`
3. Make a code change and rebuild: `make docker_image`
4. Observe that only the app stage is rebuilt, not the base stage

### Next Steps
- Monitor build times and pull times in production
- Consider further optimizations if needed
- Update documentation with the new build process
