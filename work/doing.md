# Doing

## Goal: Improve Loading UX for Label Generation

Improve the user experience by adding clear loading indicators during label generation. We'll start with this focused improvement before tackling search behavior.

### Current Issues

1. No visual feedback during label generation
2. User might click generate multiple times while processing

### Implementation Plan

Following test-first development, we'll implement these improvements in small, focused steps:

#### 1. Faster label generation

- [x] Improve performance by using tablestate.rows instead of database roundtrips.
- [ ] Refactor label generation: remove duplication from label_generation.py and bulbpicklist.py
- [ ] Analyze test coverage of lablel genration.py
- [ ] Remove unused method parameters

#### 2. Debounced Search Implementation

1. Create tests:
   - Test debounce functionality
   - Test search triggering after delay
   - Test cancellation of pending searches

2. Implementation:
   - Add debounce utility in `src/production_control/web/components/utils.py`
   - Modify search input in model_list_page component
   - Set appropriate debounce delay (300ms)

### Quality Checks

For each step:
1. Run `make test` to verify tests
2. Run `make format` for code formatting
3. Run `make quality` for linting
4. Update CHANGELOG.md in [Unreleased] section
5. Make atomic commits following conventional commits format

### Definition of Done

- All new tests pass
- Code follows project style guidelines
- Documentation updated
- CHANGELOG.md updated
- `make quality` passes
- `make releasable` passes
- Changes manually tested in development environment
- Loading indicator visible during label generation
- Button properly restored after completion

### Next Steps

1. Toggle to Act mode
2. Create test for label generation with loading state
3. Follow test-first development process
4. Make atomic commits for each logical change

### Future Improvements

After successfully implementing and learning from the label generation loading state:

1. Apply learnings to search behavior:
   - Evaluate if container-based approach works well
   - Consider debouncing for search input
   - Design proper loading feedback

2. Consider other areas that need loading states:
   - Table operations
   - Form submissions
   - Data refresh operations
