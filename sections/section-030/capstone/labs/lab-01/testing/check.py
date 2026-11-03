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


def main():
    assert one_value('node_textfile_scrape_error{job="node"}') == 0, 'The textfile collector still reports an error'
    assert one_value('inventory_items{job="node",site="a"}') == 12, 'inventory_items for site a must be 12'
    good = one_value('probe_success{job="blackbox",instance="http://probe:8080/"}')
    assert good == 1, 'The healthy target must report probe_success 1'
    bad = one_value('probe_success{job="blackbox",instance="http://probe:8080/work?status=500"}')
    assert bad == 0, 'The failing target must report probe_success 0'
    targets = json.loads(http('http://prometheus:9090/api/v1/targets'))['data']['activeTargets']
    blackbox = [t for t in targets if t['labels'].get('job') == 'blackbox']
    assert len(blackbox) == 2, 'The blackbox job must have exactly two targets'
    for target in blackbox:
        assert target['scrapeUrl'].startswith('http://blackbox-exporter:9115/probe?'), 'Each target must be scraped through the exporter /probe path'
        assert 'module=http_2xx' in target['scrapeUrl'], 'Each probe must use the http_2xx module'


finish(main)
