---
draft: true
exam_objectives:
- Instrumentation
---
# Instrumentation

The first module covers what to measure in a service and how to place the updates. The second module covers batch jobs: why a scrape cannot see them, how the Pushgateway groups and replaces metrics, and how to limit and clean up pushed data. Each module has a guided practice page, a graded lab and a summary. A Pushgateway capstone lab and a knowledge check close the section.

Read the pages of each module in order. The landing page of each module states its goals, and the summary closes it. Knowledge checks are listed separately in the course manifest.

## Learning Outcomes

- Decide what to instrument in a service: requests, queues, workers and dependencies.
- Define request metrics so that completion, errors and duration are measured together.
- Explain why pull-based collection fails for short-lived batch jobs.
- Push results to the Pushgateway with the correct path, method and labels, and clean them up.
