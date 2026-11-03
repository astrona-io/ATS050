---
draft: true
exam_objectives:
- Exporters
---
# Publish Backup Metrics Through The Textfile Collector

A backup script on the node must publish the size and the time of its last successful run through the Node Exporter.

## Starting state

A Node Exporter runs at `node-exporter:9100` in the `starfleet` namespace with the flag `--collector.textfile.directory=/textfile`. The directory is a volume from the ConfigMap `textfile`, which holds only a README file. Prometheus scrapes the exporter as the job `node` every two seconds. The `shuttle` pod has Python and can reach the exporter and Prometheus. A change to the ConfigMap reaches the exporter after the kubelet has synced the volume, which can take up to two minutes.

## Connect

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-030-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-030-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Required result

Add a metric file named `backup.prom` to the ConfigMap `textfile` in the `starfleet` namespace.

- Declare `backup_size_bytes` as a gauge with a `# HELP` line and a `# TYPE` line. Its value is 734003200 for the label `database="orders"`.
- Declare `backup_last_success_timestamp_seconds` as a gauge with the label `database="orders"` and a Unix time from the last six hours.
- Keep the existing README key in the ConfigMap.

Prometheus must return both series with `job="node"`, and `node_textfile_scrape_error` must be 0. Leave the Node Exporter and Prometheus running.
