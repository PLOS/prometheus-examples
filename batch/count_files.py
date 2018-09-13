"""
This is a silly contrived example of a batch processing job instrumented with prometheus.

"""


import os
import sys

from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway


registry = CollectorRegistry()
LAST_RUNTIME = Gauge(
    'count_files_last_successful_run', 'Last time the count_files batch job ran successfully', registry=registry
)
RUN_DURATION = Gauge('count_files_duration_seconds', 'How long it took to count files on the last run', registry=registry)
NUMBER_FILES = Gauge('count_files_count', 'How many files were counted', ['path'], registry=registry)
ERROR_COUNT = Gauge('count_files_errors', 'How many errors occurred counting files', ['path'], registry=registry)


def main(args):
    try:
        directory = args[1]
    except IndexError:
        raise SystemExit('Error: please provide a filesystem path as the first argument')
    try:
        push_gateway = args[2]
    except IndexError:
        raise SystemExit('Error: please specify your push gateway as the second argument')
    count_files(directory, push_gateway)
    LAST_RUNTIME.set_to_current_time()
    push_to_gateway(push_gateway, job='count_files', registry=registry)


@RUN_DURATION.time()
def count_files(directory, push_gateway):
    try:
        listing = os.listdir(directory)
    except FileNotFoundError:
        ERROR_COUNT.labels(path=directory).inc()
        push_to_gateway(push_gateway, job='count_files', registry=registry)
        raise SystemExit('Error: {} does not exist'.format(directory))

    files = [path for path in listing if os.path.isfile(os.path.join(directory, path))]
    NUMBER_FILES.labels(path=directory).set(len(files))
    print('Found {} files in {}'.format(len(files), directory))


if __name__ == '__main__':
    main(sys.argv)
