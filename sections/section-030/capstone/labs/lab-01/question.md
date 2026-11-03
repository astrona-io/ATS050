---
draft: true
exam_objectives:
- Exporters
---
# Exporters Capstone

The `starfleet` team must repair a broken textfile metric and add outside probes for two addresses of the `probe` application.

## Starting state

A Node Exporter runs at `node-exporter:9100` and reads the ConfigMap `textfile`. Its file `inventory.prom` holds a value that is not a number, so the textfile collector reports an error. A Blackbox Exporter runs at `blackbox-exporter:9115` and offers the module `http_2xx`, but Prometheus has no job that uses it. Prometheus reads its configuration from the ConfigMap `prometheus-config` (key `prometheus.yaml`) and was started with `--web.enable-lifecycle`, so a POST to `/-/reload` makes it read the configuration again. The `probe` application answers at `http://probe:8080/` with status 200 and at `http://probe:8080/work?status=500` with status 500. The `shuttle` pod has Python and can reach all of them.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-030-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-030-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Bring the environment to the following state.

- `node_textfile_scrape_error{job="node"}` is 0, and `inventory_items{job="node",site="a"}` is 12.
- A scrape job named `blackbox` probes `http://probe:8080/` and `http://probe:8080/work?status=500` through the Blackbox Exporter with the module `http_2xx`. Each target must be scraped from `http://blackbox-exporter:9115/probe?...`, and the `instance` label of each result must be the probed address.
- `probe_success` is 1 for the first address and 0 for the second address.
- The `blackbox` job has exactly these two targets.

Use the multi-target pattern with relabeling, and keep all existing scrape jobs.
