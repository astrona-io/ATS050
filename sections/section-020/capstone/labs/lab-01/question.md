---
draft: true
exam_objectives:
- Instrumentation
---
# Pushgateway Capstone

The batch jobs of the `starfleet` team report through the Pushgateway, and its content has drifted from what the jobs do today.

## Starting state

A Pushgateway runs at `pushgateway:9091` in the `starfleet` namespace, and Prometheus scrapes it every two seconds with `honor_labels: true`. The gateway already holds two groups. The group `job="nightly_backup",instance="db1"` has an obsolete metric `batch_legacy_rows_total` from an old version of the job. The group `job="old_cleanup",instance="x"` belongs to a job that was retired. The `shuttle` pod has Python and can reach the gateway and Prometheus.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-020-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-020-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Bring the Pushgateway to the following state.

- The group `job="nightly_backup",instance="db1"` holds a recent `batch_last_success_timestamp_seconds` (a Unix time in seconds), a positive `batch_duration_seconds`, and no `batch_legacy_rows_total`.
- The job `report_export` has failed. Its group must hold a `batch_last_failure_timestamp_seconds` with a recent Unix time, and it must not hold any success timestamp.
- The group of the retired job `old_cleanup` must be removed from the gateway.
- The series of the `probe` application in Prometheus stay untouched.

Timestamps must be less than fifteen minutes old when you submit. Choose the HTTP method for each change so that the result is exactly as described.
