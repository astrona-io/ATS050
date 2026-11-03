---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Solution: Metric Design And Cardinality Capstone

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-040/capstone/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-040-cap-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-040-cap-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Define helpers and read the current output

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
fetch_url http://legacy:8080/metrics
```

Look at the names, the `path` label and the value of the version metric. Run the command again and see that the path values change.

## Step 2: Replace the code

Save this as `legacy-code.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: legacy-code
  namespace: starfleet
data:
  app.py: |
    import http.server
    state = {'requests': 0}


    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path != '/metrics':
                self.send_response(404)
                self.end_headers()
                return
            state['requests'] += 3
            lines = ['# TYPE shop_http_requests_total counter']
            lines.append('shop_http_requests_total{method="GET",route="/orders/{id}"} %d' % state['requests'])
            lines.append('# TYPE shop_memory_bytes gauge')
            lines.append('shop_memory_bytes 536870912')
            lines.append('# TYPE shop_build_info gauge')
            lines.append('shop_build_info{version="2.4.1"} 1')
            lines.append('# TYPE shop_queue_depth gauge')
            lines.append('shop_queue_depth 7')
            body = '\n'.join(lines) + '\n'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(body.encode())


    http.server.ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
```

Apply it, restart the Deployment and wait:

```sh
kubectl apply -f legacy-code.yaml
kubectl -n starfleet rollout restart deployment/legacy
kubectl -n starfleet rollout status deployment/legacy --timeout=120s
```

Then check the result:

```sh
fetch_url http://legacy:8080/metrics
```

## Step 3: Add the sample limit

Save this as `prometheus-config.yaml`. It keeps the existing jobs and adds `sample_limit: 20` to the job `legacy`:

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
    - job_name: legacy
      sample_limit: 20
      static_configs:
      - targets:
        - legacy:8080
```

Apply it:

```sh
kubectl apply -f prometheus-config.yaml
```

The volume update can take up to about two minutes. Repeat this command until it shows the new line:

```sh
kubectl -n starfleet exec deploy/prometheus -- grep sample_limit /config/prometheus.yaml
```

Then reload Prometheus:

```sh
kubectl -n starfleet exec shuttle -- python -c "import urllib.request;print(urllib.request.urlopen(urllib.request.Request('http://prometheus:9090/-/reload',data=b'',method='POST'),timeout=8).status)"
```

Then check that the limit is active and the job is up:

```sh
fetch_url http://prometheus:9090/api/v1/status/config
kubectl -n starfleet exec shuttle -- python -c "import urllib.request;print(urllib.request.urlopen('http://prometheus:9090/api/v1/query?query=up%7Bjob%3D%22legacy%22%7D',timeout=8).read().decode())"
```

## Step 4: Grade it

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-040/capstone/labs/lab-01 --keep
```

The grader reads the endpoint twice and the running configuration of Prometheus. If it reports that the limit is missing from the running configuration, the reload did not happen after the volume update, so repeat the check and the reload.