---
draft: true
exam_objectives:
- Instrumentation
---
# Summary

Instrumentation starts from the kind of system. An online-serving system answers requests and is judged by rate, errors and duration. An offline-processing system consumes items and is judged by queue depth, throughput and waiting time. A batch job runs and ends, and it is judged by whether it succeeded and when.

The RED method describes a request path. Count completed requests with a counter and a bounded outcome label, measure duration with a histogram in seconds, and track in-progress work with a gauge that every path decrements. Place the instrumentation in one wrapper so that every route is measured the same way. Use a ratio of failures to all requests for alerts, and keep identifiers out of labels.

The USE method describes a resource: utilization, saturation and errors. A queue needs its depth, its flow in and out and its waiting time. A worker pool needs busy and total counts and a processing time. Calls to a dependency need their own counter with outcomes, including timeouts, and their own duration histogram, so that a slow dependency can be told apart from slow code.

Work that runs on a schedule is best monitored with a last-success timestamp. The age of the timestamp shows that the work stopped, whatever the reason.

Key facts:

- Count at completion so that the outcome is known.
- A ratio is a better alert signal than a raw error count.
- A percentile is estimated from histogram buckets and cannot be averaged across instances.
- Saturation, not full utilization, is what users feel.
- Record timeouts and cancelled calls as outcomes.

<!-- astrona:playground:destroy -->
