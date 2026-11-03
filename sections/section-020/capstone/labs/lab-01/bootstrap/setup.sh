#!/usr/bin/env bash
set -euo pipefail
if [[ "$(kubectl config current-context)" != "kind-astro-ats-050-lab-020-cap-01" ]]; then
  printf 'Refusing to operate on another Kubernetes context\n' >&2
  exit 1
fi
lab_directory="$(cd "$(dirname "$0")/.." && pwd)"
kubectl apply -f "$lab_directory/bootstrap/manifests/start.yaml"
kubectl -n starfleet rollout status deployment/probe --timeout=180s
kubectl -n starfleet rollout status deployment/prometheus --timeout=180s
kubectl -n starfleet rollout status deployment/traffic --timeout=180s
kubectl -n starfleet rollout status deployment/pushgateway --timeout=180s
kubectl -n starfleet wait --for=condition=Ready pod/shuttle --timeout=120s
kubectl -n outpost wait --for=condition=Ready pod/drifter --timeout=120s

kubectl -n starfleet exec -i shuttle -- python - <<'PYTHON'
import urllib.request
def push(path, body, method):
    request = urllib.request.Request('http://pushgateway:9091/metrics/' + path, data=body.encode(), method=method)
    urllib.request.urlopen(request, timeout=8).read()
push('job/nightly_backup/instance/db1', 'batch_legacy_rows_total 5\n', 'PUT')
push('job/old_cleanup/instance/x', 'batch_last_success_timestamp_seconds 1\n', 'PUT')
PYTHON
sleep 12
