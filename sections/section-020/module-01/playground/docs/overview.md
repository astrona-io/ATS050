---
draft: true
exam_objectives:
- Instrumentation
---
# Guided Practice: Rate, Errors, Duration And Last Success

In this exercise you measure the request path of the `probe` application with the RED signals, and you check how its last-success timestamp reacts to successes and failures. The probe serves its metrics at `/metrics`. A traffic generator sends one request every 0.25 seconds, and every tenth request returns status 500. Prometheus scrapes the probe every 2 seconds.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl` which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-020-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-020-01" || exit 1
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

## Find The Signals

Read the endpoint and look at the request counter and the duration histogram:

```sh
fetch_url http://probe:8080/metrics | grep -E 'lab_requests_total|lab_request_duration_seconds_count'
```

The counter has one series for each status value. The histogram count equals the sum of the two counter series, because the probe records both at the end of every request. Add the three numbers by hand from one response and confirm that they agree. If they differ by one or two, a request arrived between your readings. Read one full response and compare lines from it.

## Rate

Wait at least 30 seconds after the start, then ask for the request rate over the last minute:

```sh
run_query 'sum(rate(lab_requests_total[1m]))'
```

The traffic generator sends one request every 0.25 seconds, so the value should be close to 4 requests per second. It can be a little lower, because the generator also waits for each response.

## Error Ratio

Divide the rate of failed requests by the rate of all requests:

```sh
run_query 'sum(rate(lab_requests_total{status="500"}[1m])) / sum(rate(lab_requests_total[1m]))'
```

Every tenth request fails, so the result should be close to 0.1. Compare this ratio with the raw error rate from the query below, and explain which of the two you would put in an alert and why:

```sh
run_query 'sum(rate(lab_requests_total{status="500"}[1m]))'
```

## Duration

Calculate the average duration of requests over the last minute:

```sh
run_query 'sum(rate(lab_request_duration_seconds_sum[1m])) / sum(rate(lab_request_duration_seconds_count[1m]))'
```

The probe sleeps at least 0.01 seconds in every request, so the result is a little above 0.01.

## Create Slow Requests

Send five requests that the probe delays by 0.08 seconds, then read the buckets:

```sh
for i in 1 2 3 4 5; do fetch_url "http://probe:8080/work?status=200&delay=0.08" > /dev/null; done
fetch_url http://probe:8080/metrics | grep 'lab_request_duration_seconds_bucket'
```

Only the buckets with the bounds 0.1 and `+Inf` should have grown by five more than the buckets with the bounds 0.01 and 0.05. Five slow requests among thousands barely move an average, which is why a histogram is the better tool for slow requests.

## Check The Last Success

Read the timestamp twice and compute its age in Prometheus:

```sh
fetch_url http://probe:8080/metrics | grep '^lab_last_success_timestamp_seconds'
run_query 'time() - lab_last_success_timestamp_seconds'
```

The probe updates the timestamp on every request with status 200, and the traffic generator sends one every 0.25 seconds or so, so the age stays small. Now send a request that fails and read the timestamp again:

```sh
fetch_url "http://probe:8080/work?status=500" > /dev/null || true
fetch_url http://probe:8080/metrics | grep '^lab_last_success_timestamp_seconds'
```

A failed request does not set the timestamp, so a failure alone does not change it. Only a long period without any success makes the age grow.

## Look At The Queue Gauge

Read the queue gauge:

```sh
fetch_url http://probe:8080/metrics | grep '^lab_queue_depth'
```

Read it several times. The probe reports a fixed value, so you see no change. Think about which two additional metrics you would add to judge whether this depth is healthy, and compare your answer with the queue metrics described in the course part.

## What You Practised

You measured the rate, the error ratio and the duration of one service, saw that slow requests show up in the buckets and not in the average, and checked how a last-success timestamp behaves. The same queries work against any service that follows the same metric design.

## Common pitfalls

> [!WARNING]
> Compare lines from one response, because the counters change every 0.25 seconds. Wait at least 30 seconds before using `rate()` so that the window holds enough scrapes. A request that returns status 500 makes `fetch_url` raise an error, so the examples ignore that failure on purpose.
