---
draft: true
exam_objectives:
- Client Libraries
---
# Solution: Read The Types And Buckets Of A Live Endpoint

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-010/module-02/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-010-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-010-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Define a helper and read the endpoint

Define a helper that fetches a URL from the `shuttle` pod:

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
```

Read the lines that name the families and their types:

```sh
fetch_url http://probe:8080/metrics | grep '^# TYPE'
```

Write down each name and type. Four families start with `lab_`.

## Step 2: Read the bucket bounds

```sh
fetch_url http://probe:8080/metrics | grep 'lab_request_duration_seconds_bucket'
```

Copy the text between `le="` and `"` on each line, in order. The last one is `+Inf`.

## Step 3: Write the report

Save this as `configmap-metric-types.yaml`. Replace each `<TYPE>` with the type you wrote down in step 1, and check the bucket list against step 2:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: metric-types
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
      "histogram": "lab_request_duration_seconds",
      "bucket_bounds": ["0.01", "0.05", "0.1", "+Inf"]
    }
```

Apply it:

```sh
kubectl apply -f configmap-metric-types.yaml
```

Then check the result:

```sh
kubectl -n starfleet get configmap metric-types -o yaml
```

## Step 4: Grade it

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-010/module-02/labs/lab-01 --keep
```

The grader compares the families, the histogram name and the bounds with the live endpoint. If it fails on the families, compare your types with the `# TYPE` lines again. Counters and gauges are easy to swap.