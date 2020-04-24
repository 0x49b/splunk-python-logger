import logging
import requests

instances = []  # All running classes are stored in instances
DEFAULT_QUEUE_SIZE = 5000


class SplunkLogger(logging.Handler):
    """
    A logging HAndler ro send events to SplunkEnterprise running the Splunk HTTP Event Collector.
    """

    def __init__(self, host, port=8088, token='', index='main', allow_overrides=False, debug=False, flush_interval=15.0, force_keep_ahead=False,
                 hostname=None, protocol='https', proxies=None, queue_size=DEFAULT_QUEUE_SIZE, record_format=False, retry_backoff=2.0, retry_count=5,
                 source=None, sourcetype='text', timeout=60, verify=True):
        """
        Args:
            host (str): The Splunk host param
            port (int): The port the host is listening on
            token (str): Authentication token
            index (str): Splunk index to write to
            allow_overrides (bool): Whether to look for _<param> in log data (ex: _index)
            debug (bool): Whether to print debug console messages
            flush_interval (float): How often thread should run to push events to splunk host
            force_keep_ahead (bool): Sleep instead of dropping logs when queue fills
            hostname (str): The Splunk Enterprise hostname
            protocol (str): The web protocol to use
            proxies (list): The proxies to use for the request
            queue_size (int): The max number of logs to queue, set to 0 for no max
            record_format (bool): Whether the log record will be json
            retry_backoff (float): The requests lib backoff factor
            retry_count (int): The number of times to retry a failed request
            source (str): The Splunk source param
            sourcetype (str): The Splunk sourcetype param
            timeout (float): The time to wait for a response from Splunk
            verify (bool): Whether to perform ssl certificate validation
        """

        global instances
        instances.append(self)  # Add this instance to the instance Array to keep track of it
        logging.Handler.__init__(self)

        # Instantiation of the fields
        self.allow_overrides = allow_overrides
        self.host = host
        self.port = port
        self.token = token
        self.index = index
        self.source = source
        self.sourcetype = sourcetype
        self.verify = verify
        self.timeout = timeout
        self.flush_interval = flush_interval
        self.force_keep_ahead = force_keep_ahead
        self.log_payload = ""
        self.SIGTERM = False  # 'True' if application requested exit
        self.timer = None
        self.queue = list() # It is possible to get 'behind' and never catch up, so we limit the queue size
        self.max_queue_size = max(queue_size, 0)  # 0 is min queue size
        self.debug = debug
        self.session = requests.Session()
        self.retry_count = retry_count
        self.retry_backoff = retry_backoff
        self.protocol = protocol
        self.proxies = proxies
        self.record_format = record_format
