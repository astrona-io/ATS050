---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Remove An Unbounded Label And Fix Metric Names

The `starfleet` team owns the `legacy` application and its metrics create new series on every scrape.

## Starting state

A Python application named `legacy` runs in the namespace `starfleet` as the Deployment `legacy`. Its code is in the ConfigMap `legacy-code` under the key `app.py`, and the Deployment mounts it at `/code`. Prometheus scrapes `legacy:8080` as the job `legacy` every two seconds. The application exposes three metrics that break the rules: `shopOrdersCount` with a `user_id` label whose value is new on every scrape, `shop_checkout_latency_ms` and `shop_cache_size`. The `shuttle` pod has Python and can reach the application and Prometheus.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-040-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-040-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Change the code of the `legacy` application so that its endpoint at `/metrics` follows the naming and cardinality rules, and make the Deployment run the new code.

- The counter is named `shop_orders_total`, has the type counter and has no labels. It has at most three series.
- The label `user_id` does not appear anywhere in the output.
- The checkout duration is a gauge named `shop_checkout_duration_seconds` with the value 0.25.
- The cache size is a gauge named `shop_cache_size_bytes` with the value 1048576.
- All metric names are lower case with underscores and none ends in `_ms`.
- The set of series must not grow between two scrapes, and Prometheus must scrape the job `legacy` successfully.

Leave Prometheus unchanged.
