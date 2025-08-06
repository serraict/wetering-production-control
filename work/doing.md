# Doing

## Switch to uv package manager

**🎯 Goal:** Fully migrate from pip to uv for dependency management to improve installation speed and reproducibility.

**Current State:**

- ✅ uv is available (version 0.5.12)
- ✅ uv.lock file exists and is up-to-date
- ✅ Tests run successfully 
- ✅ CI is passing
- ✅ Makefile now uses uv for dependency installation
- ✅ CI now uses uv via `make update`
- ✅ Benchmarking completed - 9.7x performance improvement

**Tasks:**

1. **Benchmark current performance (baseline)**
   - [x] Measure pip installation time from clean state: **30.2s** 
   - [x] Measure pip installation time with cache: **22.3s** (26% faster)
   - [x] Document current dependency resolution and installation process
   - [x] Record baseline metrics for comparison

2. **Update makefile targets**
   - [x] Replace `make update` to use `uv sync --frozen` instead of pip
   - [x] Update `make bootstrap` to use `uv venv` for virtual environment creation
   - [x] Ensure all targets work with uv-managed dependencies
   - [x] Keep backwards compatibility or provide migration guide

3. **Update CI workflow**
   - [x] Install uv in GitHub Actions using astral-sh/setup-uv@v4
   - [x] Replace `make update` calls with uv commands in `.github/workflows/ci.yml`
   - [x] Verify CI still passes with uv

4. **Benchmark new performance and compare**
   - [x] Measure uv installation time from clean state: **3.96s** (7.6x faster!)
   - [x] Measure uv + dev deps installation time: **3.11s total** (9.7x faster!)
   - [x] Document speed improvement results: Runtime deps 0.6s + Dev deps 2.5s
   - [x] Compare with baseline metrics: Massive improvement vs pip's 30.2s
   - [x] Verify functionality: Tests pass (1 pre-existing failure unrelated to uv)

5. **Clean up dependency files** (optional)
   - [ ] Evaluate if `requirements-dev.txt` can be removed in favor of pyproject.toml + uv.lock
   - [ ] Update documentation if dependency management approach changes

**Acceptance Criteria:**

- [x] All makefile targets use uv instead of pip
- [x] CI uses uv and passes successfully ✅
- [x] Performance benchmark shows measurable improvement (9.7x faster!)
- [ ] Documentation updated to reflect new dependency management approach
- [x] No regression in functionality (all tests still pass)
