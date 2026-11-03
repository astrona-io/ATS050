#!/usr/bin/env python3
"""Check live state in this lab environment. Author-written and UNTESTED."""
import json
import subprocess
import sys
import time
import urllib.parse

CONTEXT = 'kind-astro-ats-050-lab-040-02-01'


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


FIXED_APP = "import http.server\nstate = {'orders': 0}\nCHECKOUT_MS = 250\nCACHE_SIZE = 1048576\n\n\nclass Handler(http.server.BaseHTTPRequestHandler):\n    def log_message(self, *args):\n        pass\n\n    def do_GET(self):\n        if self.path != '/metrics':\n            self.send_response(404)\n            self.end_headers()\n            return\n        state['orders'] += 5\n        lines = ['# TYPE shop_orders_total counter']\n        lines.append('shop_orders_total %d' % state['orders'])\n        lines.append('# TYPE shop_checkout_duration_seconds gauge')\n        lines.append('shop_checkout_duration_seconds %s' % (CHECKOUT_MS / 1000))\n        lines.append('# TYPE shop_cache_size_bytes gauge')\n        lines.append('shop_cache_size_bytes %s' % CACHE_SIZE)\n        body = '\\n'.join(lines) + '\\n'\n        self.send_response(200)\n        self.send_header('Content-Type', 'text/plain; version=0.0.4')\n        self.end_headers()\n        self.wfile.write(body.encode())\n\n\nhttp.server.ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()\n"
manifest = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'legacy-code', 'namespace': 'starfleet'},
            'data': {'app.py': FIXED_APP}}
run('kubectl', 'apply', '-f', '-', stdin=json.dumps(manifest))
run('kubectl', '-n', 'starfleet', 'rollout', 'restart', 'deployment/legacy')
run('kubectl', '-n', 'starfleet', 'rollout', 'status', 'deployment/legacy', '--timeout=120s')
