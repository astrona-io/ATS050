---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Guided Practice: Find And Limit A High Cardinality Target

In this exercise you find the metric that creates new series on every scrape, measure it with Prometheus' own tools, and then protect the server with a sample limit. The environment has a `legacy` application that Prometheus scrapes every 2 seconds, and a Prometheus server that was started with `--web.enable-lifecycle`.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl` which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-040-02)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-040-02" || exit 1
```

Define three helper functions. The first fetches a URL from inside the `shuttle` pod. The second sends an instant query to the Prometheus HTTP API. The third asks Prometheus to reload its configuration.

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
run_query() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.parse,urllib.request;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?'+urllib.parse.urlencode({'query':sys.argv[1]}),timeout=8).read().decode())" "$1"
}
reload_prometheus() {
  kubectl -n starfleet exec shuttle -- python -c "import urllib.request;print(urllib.request.urlopen(urllib.request.Request('http://prometheus:9090/-/reload',data=b'',method='POST'),timeout=8).status)"
}
```

## Read The Raw Metrics Twice

Fetch the endpoint of the `legacy` application two times, a few seconds apart:

```sh
fetch_url http://legacy:8080/metrics
fetch_url http://legacy:8080/metrics
```

Compare the lines of the metric `shopOrdersCount`. Read the label `user_id` in both outputs. Note whether the values in the second output are the same as in the first output. Then check the names against the naming rules: look at the case of the names, the unit in `shop_checkout_latency_ms` and the missing suffix on the counter.

## Measure The Scrape

Query the automatic metrics for the job:

```sh
run_query 'scrape_samples_scraped{job="legacy"}'
run_query 'scrape_series_added{job="legacy"}'
```

The first value is the number of samples in one scrape. The second is the approximate number of series that are new in the latest scrape. A value above zero in the second query on every scrape means that the application keeps creating series.

## Read The Head Block

Ask Prometheus for the number of series in the head block, twice, with a pause of about a minute between the two queries:

```sh
run_query 'prometheus_tsdb_head_series'
```

The second value should be higher than the first, because the `legacy` job adds new series continuously.

## Use The Status API

Fetch the TSDB status:

```sh
fetch_url http://prometheus:9090/api/v1/status/tsdb
```

Find the list `seriesCountByMetricName` and read the count for `shopOrdersCount`. Find the list `labelValueCountByLabelName` and read the count for `user_id`. These lists show which metric and which label have the most series and the most distinct values.

## Count The Distinct Values

Count the distinct values of the label over two different windows:

```sh
run_query 'count(last_over_time(shopOrdersCount[30s]))'
run_query 'count(last_over_time(shopOrdersCount[2m]))'
```

The second number should be larger than the first, and both should be larger than 5. A number of distinct label values that grows with the time window confirms an unbounded label.

## Add A Sample Limit

The `legacy` application returns 7 samples in one scrape. Set a limit of 5 on the job so that you can see what a violation does. Save this as `prometheus-config.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: starfleet
data:
  prometheus.yaml: |
    global:
      evaluation_interval: 2s
      scrape_interval: 2s
    rule_files:
    - /rules/*.yaml
    scrape_configs:
    - job_name: probe
      static_configs:
      - labels:
          team: starfleet
        targets:
        - probe:8080
    - job_name: prometheus
      static_configs:
      - targets:
        - localhost:9090
    - job_name: legacy
      sample_limit: 5
      static_configs:
      - targets:
        - legacy:8080
```

Apply it:

```sh
kubectl apply -f prometheus-config.yaml
```

A mounted ConfigMap reaches the pod after the kubelet has synced the volume, which can take up to about two minutes. Check what the pod sees, and repeat the command until the line `sample_limit: 5` appears:

```sh
kubectl -n starfleet exec deploy/prometheus -- grep sample_limit /config/prometheus.yaml
```

Then ask Prometheus to reload:

```sh
reload_prometheus
```

## Observe The Failure

Wait a few seconds, and then query the state of the target:

```sh
run_query 'up{job="legacy"}'
fetch_url http://prometheus:9090/api/v1/targets
```

The value of `up` should be 0. In the targets output, find the entry for the job `legacy` and read the fields `health` and `lastError`. The error should say that the sample limit was exceeded. Notice that the target does not store a partial result: the whole scrape failed.

## Restore A Safe Limit

A limit must have a margin above the normal size. Save this as `prometheus-config.yaml`, which uses a limit of 20, and apply it:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: starfleet
data:
  prometheus.yaml: |
    global:
      evaluation_interval: 2s
      scrape_interval: 2s
    rule_files:
    - /rules/*.yaml
    scrape_configs:
    - job_name: probe
      static_configs:
      - labels:
          team: starfleet
        targets:
        - probe:8080
    - job_name: prometheus
      static_configs:
      - targets:
        - localhost:9090
    - job_name: legacy
      sample_limit: 20
      static_configs:
      - targets:
        - legacy:8080
```

```sh
kubectl apply -f prometheus-config.yaml
```

When the volume has synced, reload and check `up` again:

```sh
kubectl -n starfleet exec deploy/prometheus -- grep sample_limit /config/prometheus.yaml
reload_prometheus
run_query 'up{job="legacy"}'
```

The value should return to 1. The unbounded label is still present, because only a change in the application removes it. The limit protects the server from a larger burst.

## What You Practised

You found an unbounded label by comparing two scrapes, measured it with the automatic scrape metrics, the head series gauge and the TSDB status API, and counted distinct values over growing windows. You set a sample limit that was too low and saw the whole scrape fail, and then restored a limit with a margin.

## Common pitfalls

> [!WARNING]
> A ConfigMap change reaches the pod only after the kubelet syncs the volume, so confirm the new line inside the pod before you reload. Reloading earlier changes nothing. A limit set below the normal sample count makes the target fail completely.
