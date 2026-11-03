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


import re


def sample_lines(text):
    return [line for line in text.splitlines() if line and not line.startswith('#')]


def main():
    first = http('http://legacy:8080/metrics')
    time.sleep(2)
    second = http('http://legacy:8080/metrics')
    types = family_types(second)
    assert types.get('shop_orders_total') == 'counter', 'shop_orders_total must exist with TYPE counter'
    assert types.get('shop_checkout_duration_seconds') == 'gauge', 'shop_checkout_duration_seconds must exist with TYPE gauge'
    assert types.get('shop_cache_size_bytes') == 'gauge', 'shop_cache_size_bytes must exist with TYPE gauge'
    for name in types:
        assert re.fullmatch(r'[a-z][a-z0-9_]*', name), 'Metric name is not snake_case: ' + name
        assert not name.endswith('_ms'), 'Metric name must not use milliseconds: ' + name
    assert 'user_id' not in second, 'The user_id label must be removed'
    assert len([l for l in sample_lines(second) if l.startswith('shop_orders_total')]) <= 3, 'shop_orders_total must have at most three series'
    series = lambda text: {l.rsplit(' ', 1)[0] for l in sample_lines(text)}
    assert series(second) <= series(first), 'The set of series grows between two scrapes'
    values = {l.rsplit(' ', 1)[0]: float(l.rsplit(' ', 1)[1]) for l in sample_lines(second)}
    assert values['shop_checkout_duration_seconds'] == 0.25, 'shop_checkout_duration_seconds must be 0.25'
    assert values['shop_cache_size_bytes'] == 1048576, 'shop_cache_size_bytes must be 1048576'
    assert one_value('up{job="legacy"}') == 1, 'Prometheus must scrape the legacy target successfully'


finish(main)
