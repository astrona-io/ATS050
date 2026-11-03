---
draft: true
exam_objectives:
- Instrumentation
---
# Solution: Pushgateway Capstone

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-020/capstone/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-020-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-020-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Define a helper and read the current state

Define a helper that sends a request to the Pushgateway from the `shuttle` pod:

```sh
push() {
  printf '%s\n' "$3" | kubectl -n starfleet exec -i shuttle -- python -c "import sys,urllib.request;r=urllib.request.Request('http://pushgateway:9091/metrics/'+sys.argv[2],data=sys.stdin.buffer.read(),method=sys.argv[1]);print(urllib.request.urlopen(r,timeout=8).status)" "$1" "$2"
}
```

Look at what the gateway holds for the three jobs:

```sh
kubectl -n starfleet exec shuttle -- python -c "import urllib.request;print(urllib.request.urlopen('http://pushgateway:9091/metrics',timeout=8).read().decode())" | grep -E 'nightly_backup|report_export|old_cleanup'
```

You should find the obsolete metric in the `nightly_backup` group and the `old_cleanup` group.

## Step 2: Replace the nightly_backup group

The obsolete metric must go, and PUT replaces the whole group, so push the two current metrics with PUT:

```sh
push PUT job/nightly_backup/instance/db1 "batch_last_success_timestamp_seconds $(date +%s)
batch_duration_seconds 42"
```

POST would leave `batch_legacy_rows_total` in the group, because POST replaces only the metrics named in the body.

## Step 3: Report the failure of report_export

The job has no group yet. Push a failure timestamp only:

```sh
push POST job/report_export/instance/web "batch_last_failure_timestamp_seconds $(date +%s)"
```

The group must not receive a success timestamp. If you added one by mistake, push the group again with PUT and only the failure timestamp.

## Step 4: Remove the retired group

Delete the group with the exact path that was used to create it:

```sh
push DELETE job/old_cleanup/instance/x ""
```

## Step 5: Check and grade

Wait about five seconds for a scrape, and then repeat the command from step 1. Only the expected metrics should remain. Then grade it:

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-020/capstone/labs/lab-01 --keep
```

The grader reads Prometheus. If it still finds `batch_legacy_rows_total`, the nightly_backup group was updated with POST instead of PUT. If the `old_cleanup` group is still present, the DELETE path did not match the group key.