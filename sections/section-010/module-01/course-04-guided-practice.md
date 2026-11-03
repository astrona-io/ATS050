---
draft: true
exam_objectives:
- Client Libraries
---
# Guided Practice: Read A Live Metrics Endpoint

In this exercise you read the metrics endpoint of a small instrumented application, change its counters by sending requests, and confirm in Prometheus that the changes arrive. The application is the `probe` Service in the `starfleet` namespace. It is a short Python program that writes the Prometheus text format by hand. It illustrates what a client library produces and does not use an official library.

A traffic generator sends one request every 0.25 seconds to the probe, and every tenth request asks for HTTP status 500. A Prometheus server scrapes the probe every two seconds. The `shuttle` pod has Python and can reach both Services inside the cluster.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-010-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-010-01" || exit 1
```

Keep this connection selected. Every command below targets only this environment.

## Define Two Helper Functions

Each helper runs a short Python program inside the `shuttle` pod. The first fetches a URL. The second sends an instant query to the Prometheus HTTP API.

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
run_query() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.parse,urllib.request;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?'+urllib.parse.urlencode({'query':sys.argv[1]}),timeout=8).read().decode())" "$1"
}
```

## Read The Endpoint

Fetch the metrics of the probe:

```sh
fetch_url http://probe:8080/metrics
```

Find the four metric families. Each starts with a `# HELP` line and a `# TYPE` line. Note the type of each family: a counter for requests, gauges for the queue depth and the last success time, and a histogram for the request duration. Find the label `status` on the request counter. The histogram has lines that end with `_bucket`, `_sum` and `_count`.

Notice what the endpoint does not contain. It has no per-request information and no history. It holds only current values.

## Change A Counter

Send one request that the probe counts as an error, then read the endpoint again:

```sh
fetch_url "http://probe:8080/work?status=500&delay=0.02"
fetch_url http://probe:8080/metrics
```

The value of the series with `status="500"` in the request counter is higher than before. The traffic generator also adds requests, so the increase can be larger than one. The count of the histogram also rises, because every request is observed once.

## Check The Registry Contract

Count how many distinct metric names Prometheus holds for the probe job:

```sh
run_query 'count(count by (__name__) ({job="probe"}))'
```

The result is a JSON document. The `value` field holds a timestamp and a count of families and their derived series. Compare it with the families you saw in the endpoint. The histogram contributes three names: `_bucket`, `_sum` and `_count`. The extra names such as `up` come from Prometheus itself.

## Read A Rate

A raw counter is not a rate. Ask Prometheus for the per-second rate of requests over the last 30 seconds:

```sh
run_query 'sum(rate(lab_requests_total[30s]))'
```

The traffic generator sends about four requests per second, so the value is close to that number. Now compare the error share:

```sh
run_query 'sum(rate(lab_requests_total{status="500"}[30s])) / sum(rate(lab_requests_total[30s]))'
```

The result is close to 0.1 because the generator asks for status 500 on every tenth request.

## Check A Missing Series

Ask for a label value that the application never produced:

```sh
run_query 'lab_requests_total{status="503"}'
```

The result list is empty. The series does not exist, because the code has never counted a 503. This is a missing series, not a zero. It is the reason to create known children at start-up.

## Common pitfalls

> [!WARNING]
> Confirm the kubeconfig context before you run commands. Wait at least 30 seconds after the environment starts before you use `rate()`, because a rate needs several scrapes. A raw counter value says nothing about traffic, so always compare rates.
