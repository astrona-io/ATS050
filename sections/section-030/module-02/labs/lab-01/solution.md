---
draft: true
exam_objectives:
- Exporters
---
# Solution: Publish Backup Metrics Through The Textfile Collector

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-030/module-02/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-030-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-030-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Define a helper and look at the starting state

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
fetch_url http://node-exporter:9100/metrics | grep '^node_textfile'
```

The directory has no `.prom` file yet, so there is no `node_textfile_mtime_seconds` series.

## Step 2: Create the file

The file needs the current Unix time. Print it:

```sh
date +%s
```

Save this as `configmap-backup.yaml`. Replace `<TIME>` with the number that the command printed:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: textfile
  namespace: starfleet
data:
  backup.prom: |
    # HELP backup_size_bytes Size of the last backup in bytes.
    # TYPE backup_size_bytes gauge
    backup_size_bytes{database="orders"} 734003200
    # HELP backup_last_success_timestamp_seconds Unix time of the last successful backup.
    # TYPE backup_last_success_timestamp_seconds gauge
    backup_last_success_timestamp_seconds{database="orders"} <TIME>
```

Apply it:

```sh
kubectl apply -f configmap-backup.yaml
```

Then check the result. Repeat the command until the metrics appear, which can take up to two minutes:

```sh
fetch_url http://node-exporter:9100/metrics | grep -E 'backup_|node_textfile'
```

You should see your two metrics and `node_textfile_scrape_error 0`.

## Step 3: Grade it

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-030/module-02/labs/lab-01 --keep
```

The grader reads Prometheus, so wait for the volume update and one more scrape before you submit. If the grader reports that the error gauge is not 0, a value in the file is not a number or a line is malformed. If the success timestamp is too old, replace `<TIME>` with a fresh value and apply the file again.