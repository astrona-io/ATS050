---
draft: true
exam_objectives:
- Exporters
---
# Guided Practice: Scrape Health Versus Application Health

In this exercise you read the automatic scrape metrics of the `probe` target and show that a healthy scrape can hide failing requests. The environment has the `probe` application, a traffic generator that sends one request every 0.25 seconds with every tenth request failing, and a Prometheus server that scrapes the probe every 2 seconds.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl` which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-030-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-030-01" || exit 1
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

## Read The Target State

Ask Prometheus for its list of active targets:

```sh
fetch_url http://prometheus:9090/api/v1/targets
```

Find the entry for the job `probe`. Read the fields `health`, `scrapeUrl`, `lastScrape`, `lastScrapeDuration` and `lastError`. The health should be `up`, and the last error should be empty. Note which labels the target carries.

## Read The Automatic Metrics

Query the series that Prometheus creates itself:

```sh
run_query 'up{job="probe"}'
run_query 'scrape_duration_seconds{job="probe"}'
run_query 'scrape_samples_scraped{job="probe"}'
```

`up` should be 1. The scrape duration is the time in seconds for one scrape. The sample count is the number of samples that the probe returned in the last scrape. Compare the sample count with the number of sample lines in the endpoint:

```sh
fetch_url http://probe:8080/metrics | grep -v '^#' | wc -l
```

The two numbers should be close. They can differ only if a request changed the endpoint between the commands, or if the endpoint output contains a blank line. Explain any difference before you continue.

## Show That Scrape Health Hides Failures

Query the error ratio of the application over the last minute:

```sh
run_query 'sum(rate(lab_requests_total{status="500"}[1m])) / sum(rate(lab_requests_total[1m]))'
```

Wait at least 30 seconds after the start of the environment. The ratio should be close to 0.1, while `up` is 1 for the whole period. Write one sentence that explains why both statements are true at the same time.

## Compare Two Alert Conditions

Run the condition for a missing scrape and the condition for failing work and see which one returns a result:

```sh
run_query 'up{job="probe"} == 0'
run_query 'sum(rate(lab_requests_total{status="500"}[1m])) / sum(rate(lab_requests_total[1m])) > 0.05'
```

The first query should return an empty result, and the second should return one series. An alert rule on only the first condition would never fire while requests fail.

## Detect A Missing Target

Query the expression that finds a target that has disappeared, using a job name that does not exist:

```sh
run_query 'absent(up{job="nonexistent"})'
```

The result should be one series with the value 1. Now query it for the real job:

```sh
run_query 'absent(up{job="probe"})'
```

The result should be empty, because the series exists. This is the pattern for detecting a removed target, which `up == 0` cannot detect.

## Look For A Failure Reason

Request a metric path that does not exist and read the answer. The probe serves a fixed text for unknown paths:

```sh
fetch_url http://probe:8080/does-not-exist
```

The probe answers with a plain text line and status 200. Think about what that means for a scrape job that is configured with a wrong `metrics_path`: the scrape would succeed with status 200, but the body would not contain metrics. Describe which of the automatic metrics would show this problem.

## What You Practised

You read the state of a target, the automatic scrape metrics and the application error ratio, and saw that a successful scrape does not prove that the workload is healthy. You compared two alert conditions and used `absent()` for a vanished target.

## Common pitfalls

> [!WARNING]
> Wait at least 30 seconds before using `rate()`. Do not read an empty result from a query as proof that the target is healthy. Query `up` first, because without a series for `up` the target is not configured or has not been scraped.
