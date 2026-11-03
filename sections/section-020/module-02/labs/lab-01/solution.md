---
draft: true
exam_objectives:
- Instrumentation
---
# Solution: Report A Batch Job Through The Pushgateway

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-020/module-02/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-020-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-020-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Define a helper

Define a helper that sends a request to the Pushgateway from the `shuttle` pod. It takes the HTTP method, the path after `/metrics/` and the body, and it adds the final newline that the gateway requires:

```sh
push() {
  printf '%s\n' "$3" | kubectl -n starfleet exec -i shuttle -- python -c "import sys,urllib.request;r=urllib.request.Request('http://pushgateway:9091/metrics/'+sys.argv[2],data=sys.stdin.buffer.read(),method=sys.argv[1]);print(urllib.request.urlopen(r,timeout=8).status)" "$1" "$2"
}
```

## Step 2: Push the group

Push both gauges with PUT. The group is addressed by the path, and the timestamp comes from the current time:

```sh
push PUT job/nightly_backup/instance/db1 "batch_last_success_timestamp_seconds $(date +%s)
batch_duration_seconds 42"
```

The helper prints the HTTP status code of the answer.

## Step 3: Check the result

Wait about five seconds for a scrape, and then ask Prometheus for the series:

```sh
kubectl -n starfleet exec shuttle -- python -c "import urllib.request,urllib.parse;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?'+urllib.parse.urlencode({'query':'batch_duration_seconds'}),timeout=8).read().decode())"
```

The result must contain the labels `job` and `instance` with the values from your path. If you find `exported_job` instead, the scrape job for the gateway lacks `honor_labels: true`.

## Step 4: Grade it

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-020/module-02/labs/lab-01 --keep
```

The grader checks the timestamp, the duration, the `push_time_seconds` series of the group and that no series carries an `exported_job` label. If the timestamp check fails, push again, because the value must be recent.