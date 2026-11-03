#!/usr/bin/env python3
"""Check live state in this lab environment. Author-written and UNTESTED."""
import json
import subprocess
import sys
import time
import urllib.parse

CONTEXT = 'kind-astro-ats-050-lab-040-cap-01'


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


import re


def sample_lines(text):
    return [line for line in text.splitlines() if line and not line.startswith('#')]


def main():
    first = http('http://legacy:8080/metrics')
    time.sleep(2)
    second = http('http://legacy:8080/metrics')
    types = family_types(second)
    assert types.get('shop_http_requests_total') == 'counter', 'shop_http_requests_total must exist with TYPE counter'
    assert types.get('shop_memory_bytes') == 'gauge', 'shop_memory_bytes must exist with TYPE gauge'
    assert types.get('shop_build_info') == 'gauge', 'shop_build_info must exist with TYPE gauge'
    assert types.get('shop_queue_depth') == 'gauge', 'shop_queue_depth must exist with TYPE gauge and without _total'
    for name in types:
        assert re.fullmatch(r'[a-z][a-z0-9_]*', name), 'Metric name is not snake_case: ' + name
        assert not name.endswith('MB'), 'Metric name must not carry a unit in capitals: ' + name
    assert 'path="/orders/' not in second, 'Raw URL paths with identifiers must not be label values'
    series = lambda text: {l.rsplit(' ', 1)[0] for l in sample_lines(text)}
    assert series(second) <= series(first), 'The set of series grows between two scrapes'
    values = {l.rsplit(' ', 1)[0]: float(l.rsplit(' ', 1)[1]) for l in sample_lines(second)}
    assert values['shop_memory_bytes'] == 536870912, 'shop_memory_bytes must be 536870912'
    assert values['shop_build_info{version="2.4.1"}'] == 1, 'shop_build_info{version="2.4.1"} must have the value 1'
    config = json.loads(http('http://prometheus:9090/api/v1/status/config'))['data']['yaml']
    block = config.split('job_name: legacy', 1)[1].split('- job_name:', 1)[0]
    assert 'sample_limit: 20' in block, 'The legacy scrape job must set sample_limit: 20 in the running configuration'
    assert one_value('up{job="legacy"}') == 1, 'Prometheus must scrape the legacy target successfully'


finish(main)
