#!/usr/bin/env python3
"""Check live state in this lab environment. Author-written and UNTESTED."""
import json
import subprocess
import sys
import time
import urllib.parse

CONTEXT = 'kind-astro-ats-050-lab-010-cap-01'


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


def number_check(report, key, required_names, low, high):
    entry = report[key]
    expression = entry['expression']
    at = float(entry['evaluated_at'])
    assert 0 <= time.time() - at <= 900, 'Evaluate the %s expression again: the evidence is older than fifteen minutes' % key
    for name in required_names:
        assert name in expression, 'The %s expression must use %s' % (key, name)
    assert 'rate(' in expression or 'increase(' in expression, 'The %s expression must use rate() or increase()' % key
    value = one_value(expression, at)
    assert abs(value - float(entry['value'])) <= 1e-9 + 1e-6 * abs(value), 'The reported %s value differs from the expression result' % key
    assert low <= value <= high, 'The %s value is outside the plausible range for this traffic' % key


def main():
    live_text = http('http://probe:8080/metrics')
    live = {name: kind for name, kind in family_types(live_text).items() if name.startswith('lab_')}
    report = json.loads(configmap('capstone-report')['data']['report.json'])
    assert report.get('families') == live, 'The families object does not match the live /metrics output'
    number_check(report, 'error_ratio', ['lab_requests_total'], 0.04, 0.16)
    number_check(report, 'mean_duration_seconds', ['lab_request_duration_seconds_sum', 'lab_request_duration_seconds_count'], 0.009, 0.05)
    assert report.get('error_ratio', {}).get('expression') != report.get('mean_duration_seconds', {}).get('expression'), 'Use two different expressions'


finish(main)
