---
draft: true
exam_objectives:
- Exporters
- Instrumentation
---
# Operating The Node Exporter And Choosing The Right Tool

A running Node Exporter needs the right scrape configuration, a controlled set of collectors and a plan for how batch metrics reach it. This chapter covers those points and compares the textfile collector with the Pushgateway.

## The Scrape Job

The scrape job for the Node Exporter is an ordinary job with the address of the exporter, for example port 9100 on each machine:

```yaml
scrape_configs:
  - job_name: node
    static_configs:
      - targets: ["node-exporter:9100"]
```

The `instance` label is the address of the target, so each machine has its own series. Do not set `honor_labels: true` here. The labels in the files belong to the data, and they should not replace the labels of the scrape job. If a file contains a `job` or `instance` label, a conflict arises, and the normal rule renames the label from the file to `exported_job` or `exported_instance`.

## Choosing Collectors

Check which collectors are enabled and what they cost. Use the scrape duration of each collector, and the number of series that each one adds. Some collectors are expensive on machines with many mounts or interfaces. Disable what you do not need with `--no-collector.<name>`. The reverse approach is to disable all defaults and enable only the wanted ones.

Collectors that are not enabled by default, such as those with a higher cost or less common use, require an explicit `--collector.<name>` flag.

## Filtering Within A Collector

Some collectors support flags to exclude parts of what they read. The file system collector, for example, has flags to exclude mount points and file system types. A machine that runs many containers can have hundreds of mounts that no one needs to monitor, and excluding them reduces cardinality.

## Running In Kubernetes

In a cluster, the Node Exporter usually runs as a DaemonSet, so that one pod runs on every node. The pod reads the host file systems through mounted paths, and it needs settings that let it see the host and not only the container. The textfile directory can be a mounted volume.

A ConfigMap mounted as a volume works for static or manually managed files. Kubernetes updates the files of a mounted ConfigMap after a delay, because the kubelet syncs them periodically. A change to a ConfigMap is therefore not visible in the next scrape. It appears after the sync, usually within a minute or two.

For files written by jobs, use a directory on the host, mounted into both the job and the exporter pod, so that the file written by the job is the file that the exporter reads.

## Textfile Collector Versus Pushgateway

Both approaches publish the results of short-lived jobs. They differ in several ways.

The textfile collector ties the metrics to a machine. The series carry the `instance` label of the machine, and they disappear when the machine is removed. It needs the job to run on a machine that runs the Node Exporter and to write to a directory that the exporter reads.

The Pushgateway is independent of machines. A job can push from anywhere that can reach it. The data belongs to the group, not to a machine, and it stays until deleted.

Choose the textfile collector for jobs that are part of a machine: a backup of that machine, a hardware check or a cron job on a host. Choose the Pushgateway for jobs that are not bound to a machine, such as a scheduled job in a cluster that can run on any node.

## Staleness Compared

With the textfile collector, a removed file removes its series at the next scrape. An old file keeps its series, and the modification time shows the age. With the Pushgateway, a group stays until deleted, and the age comes from the pushed timestamp and `push_time_seconds`. The two approaches require the same alert on the age of the last success.

## Security

The textfile directory feeds the exporter endpoint. Anyone who can write there can publish any metric. Use file permissions to limit this to the scripts that need it.

The endpoint of the exporter exposes system information. Limit network access to the Prometheus servers that scrape it.

## Combining With Probes

Machine-level metrics from the Node Exporter and probe results from a multi-target exporter answer different questions. The first tells how the machine behaves from inside. The second tells whether a service answers from the outside. A service can fail while its machine looks normal, and the reverse is also true, so use both views.

## Checklist For A New Textfile Metric

1. Choose a name with a prefix that belongs to your script and the unit in the name.
2. Write `# HELP` and `# TYPE` lines.
3. Write the file atomically with a temporary name and a rename.
4. Check `node_textfile_scrape_error` and `node_textfile_mtime_seconds`.
5. Find the series in Prometheus with the expected labels.
6. Add an alert on the age of the file or of the success timestamp.
7. Document who owns the script.

## Monitoring The Exporter Itself

The exporter is a target like any other, so `up` for the node job shows whether the exporter answers. Alert on `up == 0` for the job, and add `absent(up{job="node"})` to detect a job that has no targets at all.

Watch the number of samples per scrape, with `scrape_samples_scraped`. A sudden rise after a change often means that a new file or a new collector added many series. A sudden fall means that a collector or a file stopped reporting while the scrape still succeeded.

## Upgrades And Flags

Flags change between versions. When you upgrade the exporter, read the release notes for renamed collectors and metrics, because a renamed metric breaks dashboards and alert rules without any error. Test the new version on one machine and compare its metric names with the old version before you roll it out.

## What You Know Now

You can configure the scrape job for the Node Exporter, choose and restrict collectors and describe how the textfile directory is provided in a cluster. You can choose between the textfile collector and the Pushgateway for a batch job, and you have a checklist for adding a new metric.

## Common pitfalls

> [!WARNING]
> Do not set `honor_labels: true` for the Node Exporter job, because labels from a file could then override the labels of the scrape job. A change in a mounted ConfigMap appears only after the kubelet has synced it. Anyone who can write into the textfile directory can publish any metric.
