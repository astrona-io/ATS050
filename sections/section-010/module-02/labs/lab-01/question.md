---
draft: true
exam_objectives:
- Client Libraries
---
# Read The Types And Buckets Of A Live Endpoint

The `starfleet` team must document what the `probe` application exposes before it is added to a shared dashboard.

## Starting state

One instrumented probe serves metrics in the Prometheus text format. A traffic generator sends one request every 0.25 seconds, and every tenth request fails with status 500. A Prometheus server scrapes the probe every two seconds. The `shuttle` pod has Python and can reach the probe and Prometheus. No report exists yet.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-010-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-010-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Create a ConfigMap named `metric-types` in the `starfleet` namespace. It must have one key, `report.json`, whose value is a JSON object with three fields.

- `families`: an object that maps the name of every metric family that starts with `lab_` to its type, exactly as the `# TYPE` lines of `http://probe:8080/metrics` state it.
- `histogram`: the name of the one histogram family.
- `bucket_bounds`: the list of `le` values of the histogram buckets, as strings, in the order in which the endpoint lists them.

The grader reads the endpoint again and compares your report with it. Values that you invent do not pass. Keep the probe, Prometheus and the traffic generator running.
