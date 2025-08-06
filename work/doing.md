# Doing

## Switch to uv package manager

**🎯 Goal:** Fully migrate from pip to uv for dependency management to improve installation speed and reproducibility.

**Current State:**

- ✅ uv is available (version 0.5.12)
- ✅ uv.lock file exists and is up-to-date
- ✅ Tests run successfully 
- ✅ CI is passing
- ❌ Makefile still uses pip for dependency installation
- ❌ CI still uses pip via `make update`
- ❌ No benchmarking has been done

**Tasks:**

1. **Benchmark current performance (baseline)**
   - [x] Measure pip installation time from clean state: **30.2s** 
   - [x] Measure pip installation time with cache: **22.3s** (26% faster)
   - [x] Document current dependency resolution and installation process
   - [x] Record baseline metrics for comparison

2. **Update makefile targets**
   - [ ] Replace `make update` to use `uv sync` instead of pip
   - [ ] Update `make bootstrap` to use uv for virtual environment creation
   - [ ] Ensure all targets work with uv-managed dependencies
   - [ ] Keep backwards compatibility or provide migration guide

3. **Update CI workflow**
   - [ ] Install uv in GitHub Actions
   - [ ] Replace `make update` calls with uv commands in `.github/workflows/ci.yml`
   - [ ] Verify CI still passes with uv

4. **Benchmark new performance and compare**
   - [ ] Measure uv installation time from clean state
   - [ ] Measure uv installation time with cache
   - [ ] Document speed improvement results
   - [ ] Compare with baseline metrics

5. **Clean up dependency files** (optional)
   - [ ] Evaluate if `requirements-dev.txt` can be removed in favor of pyproject.toml + uv.lock
   - [ ] Update documentation if dependency management approach changes

**Acceptance Criteria:**

- [ ] All makefile targets use uv instead of pip
- [ ] CI uses uv and passes successfully
- [ ] Performance benchmark shows measurable improvement
- [ ] Documentation updated to reflect new dependency management approach
- [ ] No regression in functionality (all tests still pass)
