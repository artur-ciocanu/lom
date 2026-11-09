---
name: investigate-and-fix
description: Investigate and fix a failing test or small coding defect, then verify the change.
---

1. Reproduce the failure before changing code, and inspect the relevant code and tests.
2. Make a minimal fix for the underlying cause. Do not weaken tests to hide a failure.
3. Rerun the relevant tests and inspect the resulting changes.
4. Finish with a line beginning `Verification:` that states the test command and its result.
5. If a necessary tool or test is unavailable, say so rather than claiming success.
