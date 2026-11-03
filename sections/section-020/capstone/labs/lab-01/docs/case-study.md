---
draft: true
exam_objectives:
- Instrumentation
---
# Starting Environment

A Pushgateway runs at `pushgateway:9091` in the `starfleet` namespace, and Prometheus scrapes it every two seconds with `honor_labels: true`. The gateway already holds two groups. The group `job="nightly_backup",instance="db1"` has an obsolete metric `batch_legacy_rows_total` from an old version of the job. The group `job="old_cleanup",instance="x"` belongs to a job that was retired. The `shuttle` pod has Python and can reach the gateway and Prometheus.
