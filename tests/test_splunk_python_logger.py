import logging
import unittest

import mock
from mock import call
from mock import patch

from splunk_python_logger import SplunkLogger

# These are intentionally different than the kwarg defaults
SPLUNK_HOST = 'splunk-server.example.com'
SPLUNK_PORT = 1234
SPLUNK_TOKEN = '851A5E58-4EF1-7291-F947-F614A76ACB21'
SPLUNK_INDEX = 'test_index'
SPLUNK_HOSTNAME = 'test_host'
SPLUNK_SOURCE = 'test_source'
SPLUNK_SOURCETYPE = 'test_sourcetype'
SPLUNK_VERIFY = False
SPLUNK_TIMEOUT = 27
SPLUNK_FLUSH_INTERVAL = .1
SPLUNK_QUEUE_SIZE = 1111
SPLUNK_DEBUG = False
SPLUNK_RETRY_COUNT = 1
SPLUNK_RETRY_BACKOFF = 0.1

RECEIVER_URL = 'https://%s:%s/services/collector' % (SPLUNK_HOST, SPLUNK_PORT)


class TestSplunkHandler(unittest.TestCase):
    def setUp(self):
        self.mock_time = mock.patch('time.time', return_value=10).start()
        self.mock_request = mock.patch('requests.Session.post').start()
        self.splunk = SplunkLogger(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            token=SPLUNK_TOKEN,
            index=SPLUNK_INDEX,
            hostname=SPLUNK_HOSTNAME,
            source=SPLUNK_SOURCE,
            sourcetype=SPLUNK_SOURCETYPE,
            verify=SPLUNK_VERIFY,
            timeout=SPLUNK_TIMEOUT,
            flush_interval=SPLUNK_FLUSH_INTERVAL,
            queue_size=SPLUNK_QUEUE_SIZE,
            debug=SPLUNK_DEBUG,
            retry_count=SPLUNK_RETRY_COUNT,
            retry_backoff=SPLUNK_RETRY_BACKOFF,
        )

    def tearDown(self):
        self.splunk = None

    def test_init(self):
        self.assertIsNotNone(self.splunk)
        self.assertIsInstance(self.splunk, SplunkLogger)
        self.assertIsInstance(self.splunk, logging.Handler)
        self.assertEqual(self.splunk.host, SPLUNK_HOST)
        self.assertEqual(self.splunk.port, SPLUNK_PORT)
        self.assertEqual(self.splunk.token, SPLUNK_TOKEN)
        self.assertEqual(self.splunk.index, SPLUNK_INDEX)
        self.assertEqual(self.splunk.hostname, SPLUNK_HOSTNAME)
        self.assertEqual(self.splunk.source, SPLUNK_SOURCE)
        self.assertEqual(self.splunk.sourcetype, SPLUNK_SOURCETYPE)
        self.assertEqual(self.splunk.verify, SPLUNK_VERIFY)
        self.assertEqual(self.splunk.timeout, SPLUNK_TIMEOUT)
        self.assertEqual(self.splunk.flush_interval, SPLUNK_FLUSH_INTERVAL)
        self.assertEqual(self.splunk.max_queue_size, SPLUNK_QUEUE_SIZE)
        self.assertEqual(self.splunk.debug, SPLUNK_DEBUG)
        self.assertEqual(self.splunk.retry_count, SPLUNK_RETRY_COUNT)
        self.assertEqual(self.splunk.retry_backoff, SPLUNK_RETRY_BACKOFF)

        self.assertFalse(logging.getLogger('requests').propagate)
        self.assertFalse(logging.getLogger('splunk_handler').propagate)

    def test_splunk_worker(self):
        # Silence root logger
        log = logging.getLogger('')
        for h in log.handlers:
            log.removeHandler(h)

        log = logging.getLogger('test')
        for h in log.handlers:
            log.removeHandler(h)

        log.addHandler(self.splunk)
        log.warning('hello!')

        self.splunk.timer.join()  # Have to wait for the timer to exec

        expected_output = '{"event": "hello!", "host": "%s", "index": "%s", "source": "%s", ' \
                          '"sourcetype": "%s", "time": 10}' % \
                          (SPLUNK_HOSTNAME, SPLUNK_INDEX, SPLUNK_SOURCE, SPLUNK_SOURCETYPE)

        self.mock_request.assert_called_once_with(
            RECEIVER_URL,
            verify=SPLUNK_VERIFY,
            data=expected_output,
            timeout=SPLUNK_TIMEOUT,
            headers={'Authorization': "Splunk %s" % SPLUNK_TOKEN},
        )

    def test_splunk_worker_override(self):
        self.splunk.allow_overrides = True

        # Silence root logger
        log = logging.getLogger('')
        for h in log.handlers:
            log.removeHandler(h)

        log = logging.getLogger('test')
        for h in log.handlers:
            log.removeHandler(h)

        log.addHandler(self.splunk)
        log.warning('hello!', extra={'_time': 5, '_host': 'host', '_index': 'index'})

        self.splunk.timer.join()  # Have to wait for the timer to exec

        expected_output = '{"event": "hello!", "host": "host", "index": "index", ' \
                          '"source": "%s", "sourcetype": "%s", "time": 5}' % \
                          (SPLUNK_SOURCE, SPLUNK_SOURCETYPE)

        self.mock_request.assert_called_once_with(
            RECEIVER_URL,
            data=expected_output,
            headers={'Authorization': "Splunk %s" % SPLUNK_TOKEN},
            verify=SPLUNK_VERIFY,
            timeout=SPLUNK_TIMEOUT
        )

    def test_full_queue_error(self):
        self.splunk.allow_overrides = True
        self.splunk.max_queue_size = 10
        mock_write_log = patch.object(self.splunk, 'write_log').start()

        # Silence root logger
        log = logging.getLogger('')
        for h in log.handlers:
            log.removeHandler(h)

        log = logging.getLogger('test')
        for h in log.handlers:
            log.removeHandler(h)

        log.addHandler(self.splunk)

        for _ in range(20):
            log.warning('hello!', extra={'_time': 5, '_host': 'host', '_index': 'index'})

        self.splunk.timer.join()

        mock_write_log.assert_any_call("Log queue full; log data will be dropped.")

    def test_wait_until_empty_and_keep_ahead(self):
        self.splunk.allow_overrides = True
        self.splunk.force_keep_ahead = True
        self.splunk.max_queue_size = 10
        mock_write_log = patch.object(self.splunk, 'write_log').start()

        # Silence root logger
        log = logging.getLogger('')
        for h in log.handlers:
            log.removeHandler(h)

        log = logging.getLogger('test')
        for h in log.handlers:
            log.removeHandler(h)

        log.addHandler(self.splunk)

        # without force keep ahead, this would drop logs
        for _ in range(20):
            log.warning('hello!', extra={'_time': 5, '_host': 'host', '_index': 'index'})

        # use wait until empty instead of joining the timer
        # if this doesnt wait correctly, we'd expect to be missing calls to mock_request
        self.splunk.wait_until_empty()

        expected_output = '{"event": "hello!", "host": "host", "index": "index", ' \
                          '"source": "%s", "sourcetype": "%s", "time": 5}' % \
                          (SPLUNK_SOURCE, SPLUNK_SOURCETYPE)

        # two batches of 10 messages sent
        self.mock_request.assert_has_calls([call(
            RECEIVER_URL,
            data=expected_output * 10,
            headers={'Authorization': 'Splunk %s' % SPLUNK_TOKEN},
            verify=SPLUNK_VERIFY,
            timeout=SPLUNK_TIMEOUT
        )] * 2, any_order=True)

        # verify no logs dropped
        mock_write_log.assert_not_called()
