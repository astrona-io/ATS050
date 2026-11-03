---
draft: true
exam_objectives:
- Instrumentation
- Exporters
---
# Guided Practice: Push, Replace And Delete Groups

In this exercise you push metrics to the Pushgateway with the three HTTP methods and watch how Prometheus sees the result. The environment has a Pushgateway at `pushgateway:9091` and a Prometheus server that scrapes it every 2 seconds with `honor_labels: true`.

## Connect To The Environment

Use a host shell with the private kubeconfig for this playground. A kubeconfig is a file that tells `kubectl` which cluster and credentials to use.

<!-- astrona:playground:renew -->

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-playground-020-02)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-playground-020-02" || exit 1
```

Define three helper functions. The first sends a request to the Pushgateway from inside the `shuttle` pod. It takes the HTTP method, the path after `/metrics/` and the body. The second fetches a URL. The third runs an instant query against Prometheus.

```sh
push() {
  printf '%s\n' "$3" | kubectl -n starfleet exec -i shuttle -- python -c "import sys,urllib.request;r=urllib.request.Request('http://pushgateway:9091/metrics/'+sys.argv[2],data=sys.stdin.buffer.read(),method=sys.argv[1]);print(urllib.request.urlopen(r,timeout=8).status)" "$1" "$2"
}
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
run_query() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.parse,urllib.request;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?'+urllib.parse.urlencode({'query':sys.argv[1]}),timeout=8).read().decode())" "$1"
}
```

The helper adds a newline to the body, which the Pushgateway requires.

## Push A Group With PUT

Push two gauges to the group `job="practice_export"` and `instance="db1"`:

```sh
push PUT job/practice_export/instance/db1 'batch_duration_seconds 42
batch_rows_processed 1000'
```

The helper prints the HTTP status code of the answer. Look at what the gateway stores:

```sh
fetch_url http://pushgateway:9091/metrics | grep -E 'practice_export'
```

You should find your two metrics and the gateway's own `push_time_seconds` for the group, each with the labels `instance="db1"` and `job="practice_export"`.

## See It In Prometheus

Wait about 5 seconds for a scrape, then query:

```sh
run_query 'batch_duration_seconds{job="practice_export"}'
```

The result has the labels `job` and `instance` that you put in the path. This is the effect of `honor_labels: true`. Run a second query that would find the data if the labels had been renamed:

```sh
run_query 'batch_duration_seconds{exported_job="practice_export"}'
```

The result should be empty.

## Replace One Metric With POST

Push a new value for one metric only:

```sh
push POST job/practice_export/instance/db1 'batch_duration_seconds 51'
```

Wait for a scrape and check both metrics:

```sh
run_query 'batch_duration_seconds{job="practice_export"}'
run_query 'batch_rows_processed{job="practice_export"}'
```

The duration has the new value, and the rows metric is unchanged. POST replaced only the metric that was in the body.

## Replace The Group With PUT

Push only the duration with PUT:

```sh
push PUT job/practice_export/instance/db1 'batch_duration_seconds 60'
```

Query the rows metric after the next scrape. The series should be gone, because PUT replaced the whole group. Prometheus marks it stale after the next scrape, so the query can take a few seconds to return an empty result.

## Use A Second Group

Push to a second instance with the same job:

```sh
push PUT job/practice_export/instance/db2 'batch_duration_seconds 7'
run_query 'batch_duration_seconds{job="practice_export"}'
```

You should see two series that differ by the `instance` label. The pushes did not replace each other, because the grouping keys differ.

## Break The Rules

Send a body without a final newline. Use Python directly to avoid the helper's newline:

```sh
kubectl -n starfleet exec shuttle -- python -c "import urllib.request;r=urllib.request.Request('http://pushgateway:9091/metrics/job/practice_export/instance/db3',data=b'batch_duration_seconds 1',method='PUT');print(urllib.request.urlopen(r,timeout=8).status)"
```

The gateway should answer with an error, and Python raises an exception that shows the HTTP status. Read the message to see why the push was refused.

## Delete The Groups

Remove both groups and confirm they are gone:

```sh
push DELETE job/practice_export/instance/db1 ''
push DELETE job/practice_export/instance/db2 ''
fetch_url http://pushgateway:9091/metrics | grep -c practice_export || true
```

The count should be 0. After the next scrape, the Prometheus series also disappear.

## What You Practised

You pushed a group, saw how its labels arrive in Prometheus, compared POST with PUT, kept two groups apart with an `instance` label and removed them with DELETE.

## Common pitfalls

> [!WARNING]
> Wait at least one scrape interval before querying Prometheus after a push. A body without a final newline is refused. A PUT removes all other metrics of the group, so use POST when you only want to update one metric.
