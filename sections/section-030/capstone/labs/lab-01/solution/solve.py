#!/usr/bin/env python3
"""Check live state in this lab environment. Author-written and UNTESTED."""
import json
import subprocess
import sys
import time
import urllib.parse

CONTEXT = 'kind-astro-ats-050-lab-030-cap-01'


def run(*args, stdin=None):
    result = subprocess.run(list(args), input=stdin, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise AssertionError('Command failed: ' + ' '.join(args[:6]) + ' ' + result.stderr.strip()[:300])
    return result.stdout


def http(url, method='GET', body=None):
    script = ('import urllib.request\n'
              'request = urllib.request.Request(%r, data=%r, method=%r)\n'
              'print(urllib.request.urlopen(request, timeout=8).read().decode())\n') % (url, body, method)
    return run('kubectl', '-n', 'starfleet', 'exec', 'shuttle', '--', 'python', '-c', script)


def query(expression, at=None):
    parameters = {'query': expression}
    if at is not None:
        parameters['time'] = at
    answer = json.loads(http('http://prometheus:9090/api/v1/query?' + urllib.parse.urlencode(parameters)))
    assert answer['status'] == 'success', 'Prometheus query failed: ' + expression
    return answer['data']['result']


def one_value(expression, at=None):
    result = query(expression, at)
    assert len(result) == 1, 'Expected exactly one series for ' + expression + ' but found ' + str(len(result))
    return float(result[0]['value'][1])


def configmap(name):
    return json.loads(run('kubectl', '-n', 'starfleet', 'get', 'configmap', name, '-o', 'json'))


def family_types(text):
    types = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] == '#' and parts[1] == 'TYPE':
            types[parts[2]] = parts[3]
    return types


def finish(main):
    try:
        assert run('kubectl', 'config', 'current-context').strip() == CONTEXT, 'Refusing to operate on another Kubernetes context'
        main()
    except (AssertionError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    print('Required result verified')


inventory = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'textfile', 'namespace': 'starfleet'},
             'data': {'inventory.prom': '# TYPE inventory_items gauge\ninventory_items{site="a"} 12\n'}}
run('kubectl', 'apply', '-f', '-', stdin=json.dumps(inventory))
job = ("- job_name: blackbox\n  metrics_path: /probe\n  params:\n    module:\n    - http_2xx\n  static_configs:\n  - targets:\n"
       "    - http://probe:8080/\n    - http://probe:8080/work?status=500\n  relabel_configs:\n"
       "  - source_labels: [__address__]\n    target_label: __param_target\n"
       "  - source_labels: [__param_target]\n    target_label: instance\n"
       "  - target_label: __address__\n    replacement: blackbox-exporter:9115\n")
current = configmap('prometheus-config')['data']['prometheus.yaml']
if 'job_name: blackbox' not in current:
    manifest = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'prometheus-config', 'namespace': 'starfleet'},
                'data': {'prometheus.yaml': current.rstrip('\n') + '\n' + job}}
    run('kubectl', 'apply', '-f', '-', stdin=json.dumps(manifest))
for attempt in range(40):
    try:
        http('http://prometheus:9090/-/reload', method='POST', body=b'')
    except AssertionError:
        pass
    targets = json.loads(http('http://prometheus:9090/api/v1/targets'))['data']['activeTargets']
    if any(t['labels'].get('job') == 'blackbox' for t in targets):
        break
    time.sleep(5)
time.sleep(10)
