#!/usr/bin/env python3
"""Check live state in this lab environment. Author-written and UNTESTED."""
import json
import subprocess
import sys
import time
import urllib.parse

CONTEXT = 'kind-astro-ats-050-lab-020-cap-01'


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


now = int(time.time())
base = 'http://pushgateway:9091/metrics/job/'
http(base + 'nightly_backup/instance/db1', method='PUT',
     body=('batch_last_success_timestamp_seconds %d\nbatch_duration_seconds 42.5\n' % now).encode())
http(base + 'report_export/instance/reports', method='POST', body=('batch_last_failure_timestamp_seconds %d\n' % now).encode())
http(base + 'old_cleanup/instance/x', method='DELETE')
for attempt in range(20):
    if not query('push_time_seconds{job="old_cleanup"}') and query('batch_duration_seconds{job="nightly_backup"}'):
        break
    time.sleep(2)
