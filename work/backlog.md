# Backlog

This backlog describes the product increments we have to build to realize our product vision.

## Next

### Goal: smooth operation

- the search box behaves predictably (now key up or sth, that triggers many loads and the screen changes unpredictably)
- app clearly shows when it is working - e.g. loading data, or processing labels
- do not show unused filter controls

## Later

### Goals the user can print labels so that she can easily mark the first and last pot in a production lot

(to do: clarify)

### Goal: Improve table selection persistence

- Selection is lost when navigating between pages or changing page size
- Modify ClientStorageTableState to persist selection across pagination changes
- Update table request handling to preserve selection

### Goal: Get Paul to use this app

Paul is the lead production operator.
If we can get him to use the application, the quality of our administration will improve.
Paul does not like to sit behind the computer.
He is aware of the importance of a correct production control administration,
but his primary concern is getting the job done.

### Goal: Technical excellence

- How to do dependency injection properly (e.g. to avoid patch difficulties in the test)
- Read how fastapi does this.
- Document appropriate project structure.
- USe a templating frameweork instead string replace like we do now
- How to do validation. E.g. load invalid objects and display validation errors on screen.
  Leverage Pydantic as much as possible here
- Review build pipeline
  - Package does not seem to run tests. We should run the tests on the container.
  - Review release procedure with respect to updating the changelog (currently \[Unreleased\] section remains after release)
- Refactor and document usage of week numbering

### Goal: User can see greenhouse utilization

- [x] Leverage spacing data to calculate actual space usage
- [x] Track greenhouse area utilization changes due to spacing operations
- [ ] Display or link to the utilization graph in Superset.

### Goal: User can plan spacing scheduling details

- Build on accurate spacing tracking and utilization data
  to allow the user to plan next week's spacing operations.
- Show impact of planning changes on utilization and operations.

### Goal: Wrap up project

- Improve error message whn not connected to Dremio.
- Review the project
- Review the cookiecutter-vine-app template that we used to start this repository with.
