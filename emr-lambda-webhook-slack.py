import logging
import http.client
import urllib.parse
import json
import boto3

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)

SLACK_WEBHOOK_URLPATH = "https://hooks.slack.com/services/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"
SLACK_NOTIFICATION_CHANNEL = "#emr-webhook"


class ActiveEMRClusterChecker(object):
    logger = _logger

    def __init__(self):
        self.emr_client = None
        self.active_cluster_ids = None

    def run(self):
        self._set_emr_client()
        self._list_active_clusters()
        self._log_number_of_active_clusters()
        self._send_slack_notification_for_each_active_cluster()
        #self._terminate_active_clusters()

    def _set_emr_client(self):
        session = boto3.Session()
        self.emr_client = session.client('emr')

    def _list_active_clusters(self):
        active_cluster_states = ['STARTING', 'BOOTSTRAPPING', 'RUNNING', 'WAITING']
        response = self.emr_client.list_clusters(ClusterStates=active_cluster_states)
        self.active_cluster_ids = [cluster["Id"] for cluster in response["Clusters"]]

    def _log_number_of_active_clusters(self):
        if not self.active_cluster_ids:
            self.logger.info("No active clusters...")
        else:
            self.logger.info("Found {} active clusters...".format(len(self.active_cluster_ids)))

    def _send_slack_notification_for_each_active_cluster(self):
        if self.active_cluster_ids:
            for cluster_id in self.active_cluster_ids:
                self._send_slack_notification_for_active_cluster(cluster_id)
        else:
             self._send_slack_notification_for_active_cluster(None)

    def _send_slack_notification_for_active_cluster(self, cluster_id):
        if cluster_id is None:
            message = "No EMR cluster found with the state specified"
            icon = ":sunglasses:"
            username = "yburhan"    
        else:
            description = self._describe_cluster(cluster_id)
            message = self._get_slack_message_from_description(description)
            icon = self._get_icon_emoji_based_on_description(description)
            username = self._get_username(description)
        self._send_slack_notification(message, icon, username)

    def _describe_cluster(self, cluster_id):
        description = self.emr_client.describe_cluster(ClusterId=cluster_id)
        state = description['Cluster']['Status']['State']
        name = description['Cluster']['Name']
        keypair = description['Cluster']['Ec2InstanceAttributes']['Ec2KeyName']
        description = {'state': state, 'name': name, 'keypair': keypair}
        return description

    def _get_slack_message_from_description(self, description):
        message = "Cluster `{name}` was still active in state `{state}` with keypair `{keypair}`. " \
                  .format(state=description['state'], name=description['name'], keypair=description['keypair'])
        self.logger.info("Message: {}".format(message))
        return message

    def _get_icon_emoji_based_on_description(self, description):
        keypair = self._get_keypair(description)
        if keypair == "ghost":
            return ":ghost:"
        else:
            return ":money_with_wings:"

    def _get_username(self, description):
        keypair = self._get_keypair(description)
        username = "Active EMR Cluster Bot ({})".format(keypair)
        return username

    @staticmethod
    def _get_keypair(description):
        return description["keypair"]

    @staticmethod
    def _send_slack_notification(message, icon, username):
        slack_notifier = SlackNotifier()
        slack_notifier.send_message(message, icon, username)

    def _terminate_active_clusters(self):
        self.emr_client.terminate_job_flows(
            JobFlowIds=self.active_cluster_ids
        )
        self.logger.info("Terminated all active clusters...")


class SlackNotifier(object):
    logger = _logger

    def __init__(self):
        self.channel = SLACK_NOTIFICATION_CHANNEL
        self.slack_webhook_urlpath = SLACK_WEBHOOK_URLPATH

    def send_message(self, message, icon, username):
        payload = self._get_payload(username, icon, message)
        data = self. _get_encoded_data_object(payload)
        headers = self._get_headers()
        response = self._send_post_request(data, headers)
        self._log_response_status(response)

    def _get_payload(self, username, icon, message):
        payload_dict = {
            'channel': self.channel,
            'username': username,
            'icon_emoji': icon,
            'text': message,
            "attachments": [
                {
                    "color": "#36a64f",
                    "title": "STATUS",
                    "image_url": "https://media.giphy.com/media/dBYpAuBWrV3cA/giphy.gif"
                }
            ]
        }
        payload = json.dumps(payload_dict)
        return payload

    @staticmethod
    def _get_encoded_data_object(payload):
        values = {'payload': payload}
        str_values = {}
        for k, v in values.items():
            str_values[k] = v.encode('utf-8')
        data = urllib.parse.urlencode(str_values)
        return data

    @staticmethod
    def _get_headers():
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        return headers

    def _send_post_request(self, body, headers):
        https_connection = self._get_https_connection_with_slack()
        https_connection.request('POST', self.slack_webhook_urlpath, body, headers)
        response = https_connection.getresponse()
        return response

    @staticmethod
    def _get_https_connection_with_slack():
        h = http.client.HTTPSConnection('hooks.slack.com')
        return h

    def _log_response_status(self, response):
        if response.status == 200:
            self.logger.info("Succesfully send message to Slack.")
        else:
            self.logger.critical("Send message to Slack failed with "
                                 "status code '{}' and reason '{}'.".format(response.status, response.reason))


def lambda_handler(event, context):
    ActiveEMRClusterChecker().run()
