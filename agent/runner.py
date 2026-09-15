"""Sandboxed execution host for agent-written queries.

The agent answers data questions by writing a short Python snippet instead of
doing arithmetic in its head. That snippet runs here, in a separate `python3 -I`
process with CPU/memory/output caps, with the session's analysis and CSVs
already loaded. Anything the snippet passes to `out()` — or its last expression
— comes back as the tool result.

argv[1] is a JSON job file: {"code": str, "analysis": path, "csv_dir": path}.
The process prints one JSON object on stdout: {"ok":bool, "result":..., "stdout":str, "error":str}.
"""
import ast
import csv
import io
import json
import math
import os
import re
import resource
import statistics
import sys
from collections import Counter, OrderedDict, defaultdict
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta

CPU_SECONDS = int(os.environ.get('AGENT_SANDBOX_CPU', '30'))
ADDRESS_SPACE_BYTES = int(os.environ.get('AGENT_SANDBOX_MEM_MB', '1024')) * 1024 * 1024
MAX_RESULT_CHARS = 60000
MAX_STDOUT_CHARS = 20000


def _limit():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_BYTES, ADDRESS_SPACE_BYTES))
    except ValueError:
        pass  # some platforms refuse an AS limit; the CPU cap and the kill timer still hold
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))       # no forking out of the box
    resource.setrlimit(resource.RLIMIT_FSIZE, (5 << 20, 5 << 20))


def _json_safe(value, depth=0):
    """Make anything the snippet returns serialisable, without exploding on
    deep or cyclic structures."""
    if depth > 12:
        return str(value)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v, depth + 1) for k, v in list(value.items())[:2000]}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v, depth + 1) for v in list(value)[:2000]]
    return str(value)


def main():
    _limit()
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        job = json.load(f)

    analysis = {}
    if job.get('analysis') and os.path.exists(job['analysis']):
        with open(job['analysis'], 'r', encoding='utf-8') as f:
            analysis = json.load(f)

    csv_dir = job.get('csv_dir') or ''
    _csv_cache = {}

    def load_csv(name):
        """Rows of one uploaded CSV as dicts. `csv('sales')` or `csv('sales.csv')`."""
        key = name if name.endswith('.csv') else name + '.csv'
        if key in _csv_cache:
            return _csv_cache[key]
        path = os.path.join(csv_dir, os.path.basename(key))
        if not os.path.exists(path):
            raise FileNotFoundError(
                f'no CSV named {key}; available: {sorted(os.listdir(csv_dir)) if csv_dir else []}')
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        _csv_cache[key] = rows
        return rows

    emitted = []

    env = {
        '__builtins__': __builtins__,
        'analysis': analysis,
        'csv_rows': load_csv,
        'csv': load_csv,
        'out': emitted.append,
        'json': json, 'math': math, 're': re, 'statistics': statistics,
        'Counter': Counter, 'defaultdict': defaultdict, 'OrderedDict': OrderedDict,
        'datetime': datetime, 'date': date, 'timedelta': timedelta,
    }

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = job.get('code') or ''
            try:
                # A bare expression ("analysis['sales']['kw']['2026-07']") is the
                # commonest query shape, so evaluate it and keep the value.
                value = eval(compile(code, '<query>', 'eval'), env)
                if value is not None:
                    emitted.append(value)
            except SyntaxError:
                # Statements. A snippet that sets up variables and ends on a bare
                # expression is just as common, and a plain exec() would throw
                # that last value away — so run the body, then evaluate the
                # trailing expression the way a REPL would.
                tree = ast.parse(code, '<query>', 'exec')
                tail = None
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    tail = ast.Expression(tree.body.pop().value)
                exec(compile(tree, '<query>', 'exec'), env)
                if tail is not None:
                    value = eval(compile(tail, '<query>', 'eval'), env)
                    if value is not None:
                        emitted.append(value)
                if not emitted and 'result' in env:
                    emitted.append(env['result'])
    except Exception as exc:  # noqa: BLE001 — the message is the tool result
        print(json.dumps({
            'ok': False,
            'error': f'{type(exc).__name__}: {exc}',
            'stdout': buf.getvalue()[:MAX_STDOUT_CHARS],
        }))
        return

    result = emitted[0] if len(emitted) == 1 else (emitted or None)
    payload = json.dumps({
        'ok': True,
        'result': _json_safe(result),
        'stdout': buf.getvalue()[:MAX_STDOUT_CHARS],
    })
    if len(payload) > MAX_RESULT_CHARS:
        payload = json.dumps({
            'ok': False,
            'error': (f'result is {len(payload)} chars, over the {MAX_RESULT_CHARS} limit — '
                      'aggregate or slice it in the query instead of returning raw rows'),
            'stdout': buf.getvalue()[:2000],
        })
    print(payload)


if __name__ == '__main__':
    main()
