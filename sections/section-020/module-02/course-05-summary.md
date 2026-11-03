---
draft: true
exam_objectives:
- Instrumentation
- Exporters
---
# Summary

Prometheus pulls metrics, and a short-lived batch job can start and end between two scrapes. The Pushgateway solves this for service-level batch jobs: the job pushes its metrics at the end of a run, the gateway keeps them, and Prometheus scrapes the gateway. It is not a replacement for scraping long-running services.

A push goes to a path that carries the `job` label and optional further labels, and these labels form the grouping key. The body is the text format and must end with a newline. PUT replaces the whole group, POST replaces only the metrics named in the body and DELETE removes the group. The gateway adds `push_time_seconds` and `push_failure_time_seconds` for each group.

The scrape job for the gateway needs `honor_labels: true`. Without it, Prometheus renames the pushed `job` and `instance` labels to `exported_job` and `exported_instance`. The metric `up` describes only the gateway, never the batch jobs.

The gateway never expires data, does not aggregate and has no access control by itself. Push gauges for the results of a run, include a last-success timestamp, alert on its age and delete the groups of retired jobs.

Key facts:

- Use the Pushgateway for jobs that are not tied to one machine.
- Pushed samples cannot carry explicit timestamps.
- POST updates named metrics, and PUT replaces the group.
- Alert on the age of a timestamp, not on the presence of a value.
- Remove stale groups with DELETE.

<!-- astrona:playground:destroy -->
