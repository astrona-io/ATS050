---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Metric Design And Cardinality Capstone

The `starfleet` team must repair the metric design of the `legacy` application and protect Prometheus against a repeat.

## Starting state

A Python application named `legacy` runs as the Deployment `legacy` in the namespace `starfleet`. Its code is in the ConfigMap `legacy-code` under the key `app.py`. Prometheus scrapes it as the job `legacy` every two seconds. The configuration is in the ConfigMap `prometheus-config` under the key `prometheus.yaml`, and Prometheus runs with `--web.enable-lifecycle`, so a POST to `/-/reload` makes it read the configuration again. The application exposes `Http_Requests` with the labels `path` and `method` where each path holds a new order number, a gauge `memoryMB` with the value 512, a gauge `build_version` that holds the version in a label and a number in the value, and a gauge `queue_depth_total`. The `shuttle` pod has Python and can reach both services.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-040-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-040-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Bring the environment to the following state.

- The endpoint exposes `shop_http_requests_total` with the type counter, `shop_memory_bytes` with the value 536870912, `shop_build_info` with the type gauge and `shop_queue_depth` with the type gauge. All names are lower case with underscores.
- The request counter has the labels `method` and `route`, and the route holds the template `/orders/{id}`, not a real order number.
- The build version is exposed as `shop_build_info{version="2.4.1"}` with the value 1.
- The set of series does not grow between two scrapes.
- The scrape job `legacy` has `sample_limit: 20` in the running configuration of Prometheus, and the job is up.

Keep the existing jobs `probe` and `prometheus` unchanged.
