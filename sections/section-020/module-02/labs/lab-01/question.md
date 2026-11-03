---
draft: true
exam_objectives:
- Instrumentation
---
# Report A Batch Job Through The Pushgateway

The `nightly_backup` job for the database `db1` ends before Prometheus can scrape it. The team needs its last result to be available in Prometheus.

## Starting state

A Pushgateway runs at `pushgateway:9091` in the `starfleet` namespace. A Prometheus server scrapes it every two seconds with `honor_labels: true`, and also scrapes the `probe` application. The `shuttle` pod has Python and can reach the Pushgateway and Prometheus. The nightly backup job has never reported: the gateway holds no group for it.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-020-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-020-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Push the result of the backup to the Pushgateway at `http://pushgateway:9091`.

- Use the grouping labels `job="nightly_backup"` and `instance="db1"`.
- Push a gauge `batch_last_success_timestamp_seconds` that holds the current Unix time in seconds.
- Push a gauge `batch_duration_seconds` that holds a positive number of seconds.

Prometheus must return both series with the labels `job="nightly_backup"` and `instance="db1"`. Labels must not be renamed to `exported_job`. The timestamp must be less than fifteen minutes old when you submit. Leave the Pushgateway, Prometheus and the `probe` application running.
