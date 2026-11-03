---
draft: true
exam_objectives:
- Exporters
---
# Solution: Exporters Capstone

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-030/capstone/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-030-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-030-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Define helpers and look at the problem

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
fetch_url http://node-exporter:9100/metrics | grep '^node_textfile'
kubectl -n starfleet get configmap textfile -o yaml
```

The file `inventory.prom` has the value `twelve`, which is not a number. The error gauge should be 1.

## Step 2: Repair the file

Save this as `configmap-textfile.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: textfile
  namespace: starfleet
data:
  inventory.prom: |
    # HELP inventory_items Number of inventory items.
    # TYPE inventory_items gauge
    inventory_items{site="a"} 12
```

Apply it:

```sh
kubectl apply -f configmap-textfile.yaml
```

The volume update can take up to two minutes. Then check that `node_textfile_scrape_error` is 0:

```sh
fetch_url http://node-exporter:9100/metrics | grep -E 'inventory_items|node_textfile_scrape_error'
```

## Step 3: Read the current Prometheus configuration

```sh
kubectl -n starfleet get configmap prometheus-config -o jsonpath='{.data.prometheus\.yaml}'
```

Copy the text. It holds the jobs `probe`, `prometheus` and `node`.

## Step 4: Add the blackbox job

Save this as `configmap-prometheus-config.yaml`. Keep the existing jobs exactly as you copied them, and add the job `blackbox` at the end of the list:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: starfleet
data:
  prometheus.yaml: |
    global:
      evaluation_interval: 2s
      scrape_interval: 2s
    rule_files:
    - /rules/*.yaml
    scrape_configs:
    - job_name: probe
      static_configs:
      - labels:
          team: starfleet
        targets:
        - probe:8080
    - job_name: prometheus
      static_configs:
      - targets:
        - localhost:9090
    - job_name: node
      static_configs:
      - targets:
        - node-exporter:9100
    - job_name: blackbox
      metrics_path: /probe
      params:
        module:
        - http_2xx
      static_configs:
      - targets:
        - http://probe:8080/
        - http://probe:8080/work?status=500
      relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

Apply it:

```sh
kubectl apply -f configmap-prometheus-config.yaml
```

## Step 5: Reload Prometheus

The mounted file changes after the kubelet has synced the volume. Define a helper that sends the reload request, and run it:

```sh
reload_prometheus() {
  kubectl -n starfleet exec shuttle -- python -c "import urllib.request;r=urllib.request.Request('http://prometheus:9090/-/reload',data=b'',method='POST');print(urllib.request.urlopen(r,timeout=8).status)"
}
reload_prometheus
```

Then check whether Prometheus now lists the job. Repeat the reload and the check every 20 seconds until it appears:

```sh
fetch_url http://prometheus:9090/api/v1/targets | grep -o '"job":"blackbox"' | sort | uniq -c
```

Two lines of output with the job name mean that both targets are active.

## Step 6: Check the probes

Wait for one more scrape and ask for the results:

```sh
kubectl -n starfleet exec shuttle -- python -c "import urllib.request,urllib.parse;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?'+urllib.parse.urlencode({'query':'probe_success{job=\"blackbox\"}'}),timeout=8).read().decode())"
```

The first address should report 1, and the second address should report 0.

## Step 7: Grade it

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-030/capstone/labs/lab-01 --keep
```

If the grader finds a different number of targets, check that you copied the list exactly. If a scrape URL does not start with the exporter address, a relabeling rule is wrong or missing. If `probe_success` is missing, Prometheus has not reloaded the configuration yet, so repeat step 5.