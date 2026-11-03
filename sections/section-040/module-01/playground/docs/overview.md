---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Guided Practice: Review The Probe Metrics Against The Rules

In this exercise you read the metric names and labels of the `probe` application and judge each one against the naming rules. The environment has the `probe` application, a traffic generator that sends one request every 0.25 seconds with every tenth request failing, and a Prometheus server that scrapes the probe every 2 seconds.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl` which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-040-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-040-01" || exit 1
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

## Read The Names

Fetch the endpoint and list only the type lines:

```sh
fetch_url http://probe:8080/metrics | grep '^# TYPE'
```

For each metric, check three things. Does the name carry the unit as a base unit? Does a counter end in `_total`? Does the type match the meaning of the quantity? Write down your verdict for `lab_requests_total`, `lab_queue_depth`, `lab_last_success_timestamp_seconds` and `lab_request_duration_seconds`.

## Read The Labels

Print the lines of the request counter:

```sh
fetch_url http://probe:8080/metrics | grep '^lab_requests_total'
```

Read the label names and the values of `status`. Decide whether the set of values is bounded and listable. Decide whether the sum over all statuses is a meaningful number.

## Count The Series

Ask Prometheus how many series exist per metric name for the job:

```sh
run_query 'count by (__name__) ({job="probe"})'
```

Compare the count for each name with the number of label combinations that you expect from the previous step. A difference means a label that you did not notice.

For the histogram, work out the expected count by hand. It has one series for each bucket boundary, including the final `+Inf` bucket, plus one `_sum` and one `_count` series. Compare your number with the result for the three names `lab_request_duration_seconds_bucket`, `lab_request_duration_seconds_sum` and `lab_request_duration_seconds_count`.

## Test The Sum Rule

Query the total request rate by summing over the status label, and then the failure share:

```sh
run_query 'sum(rate(lab_requests_total[1m]))'
run_query 'sum(rate(lab_requests_total{status="500"}[1m])) / sum(rate(lab_requests_total[1m]))'
```

Wait at least 30 seconds after the start of the environment. The first result is the total request rate, which shows that the sum over the label is meaningful. The second result should be close to 0.1.

## Test The Gauge Rule

Query the queue gauge directly, and then try to apply `rate()` to it:

```sh
run_query 'lab_queue_depth'
run_query 'rate(lab_queue_depth[1m])'
```

The first query returns the current level. The second returns a value that describes the change of the level, which is not what the metric is for. Write one sentence on why `rate()` belongs only on counters.

## Check The Reserved Labels

Look at the labels that Prometheus attached to the series from the first query. Identify which labels came from the application and which came from the scrape. Confirm that the application does not define `job` or `instance` itself.

## What You Practised

You judged names, types and units against the rules, counted series against the expected label combinations, and tested that the sum over a label is meaningful for a counter and that `rate()` is meaningful only for counters.

## Common pitfalls

> [!WARNING]
> Wait at least 30 seconds before using `rate()`. An empty result from `count by (__name__)` means the target is not scraped yet, so query `up{job="probe"}` first.
