---
draft: true
exam_objectives:
- Exporters
- Instrumentation
---
# Guided Practice: Publish, Break And Repair A Metric File

In this exercise you publish a metric file through the textfile collector, watch Prometheus pick it up, break the file on purpose and repair it. The environment has a Node Exporter at `node-exporter:9100` that reads the directory `/textfile`, a ConfigMap named `textfile` that provides the files in that directory and a Prometheus server that scrapes the exporter as the job `node` every 2 seconds.

A ConfigMap that is mounted as a volume is updated by the kubelet with a delay. After each change, wait up to two minutes before you expect to see it in the exporter output.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl` which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-030-02)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-030-02" || exit 1
```

Define two helper functions. The first fetches a URL from inside the `shuttle` pod. The second sends an instant query to the Prometheus HTTP API.

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
run_query() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.parse,urllib.request;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?'+urllib.parse.urlencode({'query':sys.argv[1]}),timeout=8).read().decode())" "$1"
}
```

## Read The Starting State

Look at the files that the collector knows and at its error gauge:

```sh
fetch_url http://node-exporter:9100/metrics | grep -E '^node_textfile|^node_scrape_collector_success\{collector="textfile"\}'
```

At the start, the directory holds only a README file, which does not end in `.prom`, so no file is listed. Check that `node_textfile_scrape_error` is 0, and that `node_scrape_collector_success` for the textfile collector is 1.

## Publish A File

Save this as `configmap-textfile.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: textfile
  namespace: starfleet
data:
  demo.prom: |
    # HELP demo_items Number of demo items.
    # TYPE demo_items gauge
    demo_items{site="a"} 5
    demo_items{site="b"} 7
```

Apply it:

```sh
kubectl apply -f configmap-textfile.yaml
```

Then check the result. Repeat the command until the metric appears, which can take up to two minutes:

```sh
fetch_url http://node-exporter:9100/metrics | grep -E 'demo_items|node_textfile_mtime_seconds'
```

You should find two `demo_items` series and one `node_textfile_mtime_seconds` series with the label `file` set to your file.

## Find It In Prometheus

```sh
run_query 'demo_items'
```

The series carry the labels `site` from the file, and `job` and `instance` from the scrape job. Compare the `instance` label with the address of the exporter.

## Check The File Age

```sh
run_query 'time() - node_textfile_mtime_seconds'
```

The result is the age of each file in seconds. Note that for a file in a ConfigMap, the modification time reflects the time of the volume update and can differ from the time when you applied the change.

## Break The File

Add a second file with a value that is not a number. A merge patch adds the key and leaves the other keys alone:

```sh
kubectl -n starfleet patch configmap textfile --type merge -p '{"data":{"broken.prom":"# TYPE broken_items gauge\nbroken_items{site=\"a\"} twelve\n"}}'
```

Wait for the volume update and read the error gauge:

```sh
fetch_url http://node-exporter:9100/metrics | grep -E 'node_textfile_scrape_error'
```

The error gauge should become 1. Query it in Prometheus as well:

```sh
run_query 'node_textfile_scrape_error'
```

Note that `up` for the job stays at 1 during this time. Run `run_query 'up{job="node"}'` to confirm it.

## Repair The File

Remove the broken file from the ConfigMap with a merge patch that sets its key to null:

```sh
kubectl -n starfleet patch configmap textfile --type merge -p '{"data":{"broken.prom":null}}'
```

Wait for the volume update and check that the error gauge returns to 0:

```sh
fetch_url http://node-exporter:9100/metrics | grep -E 'node_textfile_scrape_error'
```

## Clean Up

Remove the demo file as well and confirm that its series disappear after the next scrape:

```sh
kubectl -n starfleet patch configmap textfile --type merge -p '{"data":{"demo.prom":null}}'
```

## What You Practised

You published a file through the textfile collector and found its series in the exporter and in Prometheus. You broke the file with a value that is not a number, saw the error gauge change while `up` stayed at 1, and repaired it.

## Common pitfalls

> [!WARNING]
> A change to a mounted ConfigMap appears only after the kubelet has synced the volume, so wait up to two minutes. Use a merge patch to add or change one key without touching the others, and set a key to null to remove it. Do not read `up` as proof that the files are valid.
