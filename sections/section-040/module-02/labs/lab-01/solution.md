---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Solution: Remove An Unbounded Label And Fix Metric Names

This walkthrough solves the task in steps. After each step you can grade your work with `astrona submit`. The grader reads the live state of the environment again, so a result that you typed by hand and that does not match the live state does not pass. The author has not run this lab yet, so no command output is shown.

Start the lab if it is not running:

```sh
astrona run --git ssh://git@github.com/astrona-io/ATS050.git -c section-040/module-02/labs/lab-01
```

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig is a file that tells `kubectl`, the Kubernetes command-line tool, which cluster and credentials to use.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-040-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-040-02-01" || exit 1
```

Keep this connection selected. Every command in this task targets only this environment.

## Step 1: Define a helper and read the current output

```sh
fetch_url() {
  kubectl -n starfleet exec shuttle -- python -c "import sys,urllib.request;print(urllib.request.urlopen(sys.argv[1],timeout=8).read().decode())" "$1"
}
fetch_url http://legacy:8080/metrics
fetch_url http://legacy:8080/metrics
```

Compare the two outputs. The `user_id` values change, so each scrape creates five new series.

## Step 2: Read the current code

```sh
kubectl -n starfleet get configmap legacy-code -o jsonpath='{.data.app\.py}'
```

The code builds one line for each of five users on every request and uses a counter name in camel case.

## Step 3: Replace the code

Save this as `legacy-code.yaml`. It replaces the key `app.py` with a version that exposes one counter without labels, converts the duration to seconds and renames the cache size with its unit:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: legacy-code
  namespace: starfleet
data:
  app.py: |
    import http.server
    state = {'orders': 0}
    CHECKOUT_MS = 250
    CACHE_SIZE = 1048576


    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path != '/metrics':
                self.send_response(404)
                self.end_headers()
                return
            state['orders'] += 5
            lines = ['# TYPE shop_orders_total counter']
            lines.append('shop_orders_total %d' % state['orders'])
            lines.append('# TYPE shop_checkout_duration_seconds gauge')
            lines.append('shop_checkout_duration_seconds %s' % (CHECKOUT_MS / 1000))
            lines.append('# TYPE shop_cache_size_bytes gauge')
            lines.append('shop_cache_size_bytes %s' % CACHE_SIZE)
            body = '\n'.join(lines) + '\n'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(body.encode())


    http.server.ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
```

Apply it:

```sh
kubectl apply -f legacy-code.yaml
```

A pod does not reload a mounted file as a new program, so restart the Deployment and wait for it:

```sh
kubectl -n starfleet rollout restart deployment/legacy
kubectl -n starfleet rollout status deployment/legacy --timeout=120s
```

Then check the result:

```sh
fetch_url http://legacy:8080/metrics
```

You should see the three new names, no `user_id` label and a counter that grows by five on each request.

## Step 4: Grade it

```sh
astrona submit --git ssh://git@github.com/astrona-io/ATS050.git -c section-040/module-02/labs/lab-01 --keep
```

The grader reads the live endpoint twice and queries Prometheus again. If it reports that `up` is not 1, wait a few seconds for the next scrape and submit again. If it reports a missing name, check the spelling in the TYPE lines.