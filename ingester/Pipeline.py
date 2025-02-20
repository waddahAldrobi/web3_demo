import json


class Pipeline:
    def __init__(self, path):
        # Load configuration
        with open(path, "r") as config_file:
            self.config = json.load(config_file)

        self.rpc = self.config["ethereum_rpc_url"]
        self.pool_address = self.config["pool_address"]
        self.kafka_topic = self.config["kafka_topic"]
        self.poll_interval = self.config["poll_interval"]
        self.abi = self.config["abi"]
        self.schema = self.config["schema"]
