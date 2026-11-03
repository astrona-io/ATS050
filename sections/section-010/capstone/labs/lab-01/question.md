---
draft: true
exam_objectives:
- Client Libraries
---
# Client Libraries Capstone

The `starfleet` team wants one evidence report that proves it understands the metric types of the `probe` application and can compute two service indicators from them.

## Starting state

One instrumented probe serves metrics in the Prometheus text format. A traffic generator sends one request every 0.25 seconds, and every tenth request fails with status 500. A Prometheus server scrapes the probe every two seconds. The `shuttle` pod has Python and can reach the probe and Prometheus. No report exists yet.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-010-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-010-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Create a ConfigMap named `capstone-report` in the `starfleet` namespace with the key `report.json`. The value is a JSON object with three fields.

- `families`: an object that maps each `lab_` metric family name to its type, as the endpoint `http://probe:8080/metrics` states it.
- `error_ratio`: an object with `expression`, `evaluated_at` and `value`. The expression is a PromQL (Prometheus Query Language) query for the share of requests that return status 500, calculated from rates of the request counter.
- `mean_duration_seconds`: an object with the same three fields. The expression calculates the mean request duration from the rates of the histogram `_sum` and `_count` series.

`evaluated_at` is the Unix time in seconds at which you ran the query, and it must be less than fifteen minutes old when you submit. `value` is the number that Prometheus returned. The grader runs your expression again at your `evaluated_at` time, compares the value and checks that it is plausible for this traffic.
