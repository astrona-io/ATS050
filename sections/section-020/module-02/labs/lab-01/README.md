# Push The Result Of A Batch Job

Status: UNTESTED. The files were checked statically (`astrona validate`, `bash -n`, syntax checks) but the environment, the reference solution and the grader were never run.

The task is in `question.md` and the walkthrough is in `solution.md`. `testing/smoke.sh` is the author check: it expects the grader to fail on the starting state, applies `solution/apply.sh` and expects the grader to pass.
