---
draft: true
exam_objectives:
- Client Libraries
---
# Guided Practice: Types, Buckets And Rates On A Live Endpoint

In this exercise you read the families of the `probe` application, calculate with its histogram buckets and compare your results with Prometheus. The probe writes the classic text format by hand. A traffic generator sends one request every 0.25 seconds, and every tenth request returns status 500.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl` which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-010-02)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-010-02" || exit 1
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

## List The Types

Read the endpoint and keep only the `# TYPE` lines:

```sh
fetch_url http://probe:8080/metrics | grep '^# TYPE'
```

Write down each family name and its type. You should find a counter, two gauges and a histogram. The counter name ends in `_total`, and the histogram name ends in `_seconds`. These endings follow the naming conventions for counters and for durations.

## Read The Buckets

Show only the bucket lines of the duration histogram:

```sh
fetch_url http://probe:8080/metrics | grep 'lab_request_duration_seconds_bucket'
```

Check three properties. The values never decrease from one line to the next. The last line has `le="+Inf"`. Its value equals the value of `lab_request_duration_seconds_count`, which you can show with another `grep`. If your numbers do not match, the endpoint changed between the two commands, because the traffic generator keeps sending requests. Read the whole output once and compare lines from the same response.

## Calculate An Average

The average request duration over the last minute is the rate of the sum divided by the rate of the count:

```sh
run_query 'sum(rate(lab_request_duration_seconds_sum[1m])) / sum(rate(lab_request_duration_seconds_count[1m]))'
```

The probe sleeps for 0.01 seconds in every request, so the result is a little above 0.01.

## Find The Share Within A Bound

Ask what share of requests finished within 0.05 seconds:

```sh
run_query 'sum(rate(lab_request_duration_seconds_bucket{le="0.05"}[1m])) / sum(rate(lab_request_duration_seconds_count[1m]))'
```

Because the probe never delays a request longer than 0.1 seconds and normally uses 0.01, the result is close to 1.

## Estimate A Percentile

Estimate the 95th percentile with the bucket rates:

```sh
run_query 'histogram_quantile(0.95, sum by (le) (rate(lab_request_duration_seconds_bucket[1m])))'
```

The probe sleeps for 0.01 seconds plus a small overhead, so almost every request lands in the bucket above 0.01 and up to 0.05. The answer is an interpolated value inside that bucket. Compare it with the average above. The estimate cannot be more precise than the width of the bucket that it falls in.

## Send A Slow Request

Send a request that the probe delays by 0.08 seconds, and read the buckets again:

```sh
fetch_url "http://probe:8080/work?status=200&delay=0.08"
fetch_url http://probe:8080/metrics | grep 'lab_request_duration_seconds_bucket'
```

The buckets with a bound of 0.1 and `+Inf` count the new request, while the buckets with the bounds 0.01 and 0.05 do not. This shows that buckets are cumulative.

## Common pitfalls

> [!WARNING]
> Compare bucket lines from one response, because the endpoint changes while traffic arrives. Wait at least 30 seconds after the start before you use `rate()`. A percentile from this histogram is an estimate and depends on the bucket bounds.
