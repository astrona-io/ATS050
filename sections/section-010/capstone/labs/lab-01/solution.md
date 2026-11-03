---
draft: true
exam_objectives:
- Client Libraries
---
# Solution: Client Libraries Capstone

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-010/capstone/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-010-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-010-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Helpers

Define two helpers:
```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
run_query() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.parse,urllib.request;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?'+urllib.parse.urlencode({'query':sys.argv[1]}),timeout=8).read().decode())" "$1"
}
```

## Step 2: Read the families

```sh
fetch_url http://probe:8080/metrics | grep '^# TYPE'
```

## Step 3: Run the two queries

Wait at least 30 seconds after the start so that Prometheus has several scrapes. Then run:

```sh
run_query 'sum(rate(lab_requests_total{status="500"}[1m])) / sum(rate(lab_requests_total[1m]))'
run_query 'sum(rate(lab_request_duration_seconds_sum[1m])) / sum(rate(lab_request_duration_seconds_count[1m]))'
date +%s
```

In each response, the `value` field holds two items. The first is the evaluation time and the second is the number as a string. The error ratio should be close to 0.1, and the mean duration should be a little above 0.01 seconds.

## Step 4: Write the report

Save this as `configmap-capstone-report.yaml`. Replace each `<TYPE>`, `<TIME>` and `<VALUE>` with the data you collected. Use the same time for both queries, taken from the `date +%s` command, and keep the numbers numeric:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: capstone-report
  namespace: starfleet
data:
  report.json: |
    {
      "families": {
        "lab_last_success_timestamp_seconds": "<TYPE>",
        "lab_queue_depth": "<TYPE>",
        "lab_request_duration_seconds": "<TYPE>",
        "lab_requests_total": "<TYPE>"
      },
      "error_ratio": {
        "expression": "sum(rate(lab_requests_total{status=\"500\"}[1m])) / sum(rate(lab_requests_total[1m]))",
        "evaluated_at": <TIME>,
        "value": <VALUE>
      },
      "mean_duration_seconds": {
        "expression": "sum(rate(lab_request_duration_seconds_sum[1m])) / sum(rate(lab_request_duration_seconds_count[1m]))",
        "evaluated_at": <TIME>,
        "value": <VALUE>
      }
    }
```

Apply it:

```sh
kubectl apply -f configmap-capstone-report.yaml
```

## Step 5: Grade it

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-010/capstone/labs/lab-01 --keep
```

The grader runs your expressions at your `evaluated_at` time. A `value` that you rounded can differ slightly from the exact number, so copy it in full. If the grader says the evidence is too old, run the queries again and update the report.