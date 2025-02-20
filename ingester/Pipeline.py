import json
import os
from web3 import Web3
from web3.types import BlockData
from confluent_kafka import Producer

KAFKA_BROKER = "kafka:9092"


class Pipeline:
    """Processes Ethereum blocks and sends transformed event data to Kafka."""

    def __init__(self, config_name: str):
        """
        Initializes the pipeline with Ethereum RPC, contract details, and Kafka producer.

        Args:
            config_name (str): Name of the configuration file (without extension).
        """
        self.config_name = config_name
        self.config = self._load_config(config_name)
        self.rpc = self.config["ethereum_rpc_url"]
        self.pool_address = Web3.to_checksum_address(self.config["pool_address"])
        self.kafka_topic = self.config["kafka_topic"]
        self.poll_interval = self.config["poll_interval"]
        self.abi = self.config["abi"]
        self.schema = self.config["schema"]

        self.web3 = Web3(Web3.HTTPProvider(self.rpc))
        if not self.web3.is_connected():
            raise ConnectionError("Connection to RPC failed.")
        print("Connected to RPC!")

        self.contract = self.web3.eth.contract(address=self.pool_address, abi=self.abi)
        self.producer = Producer({"bootstrap.servers": KAFKA_BROKER})

        self.transformations = {
            "uniswap_swap": to_uniswap_swap,
        }

    def _load_config(self, config_name: str) -> dict:
        """
        Loads the configuration from a JSON file.

        Args:
            config_name (str): Configuration file name (without extension).

        Returns:
            dict: Parsed configuration data.
        """
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"configs/{config_name}.json"
        )
        with open(path, "r") as config_file:
            return json.load(config_file)

    def send_message(self, key: str, value: dict):
        """
        Sends a message to Kafka.

        Args:
            key (str): Message key.
            value (dict): Message payload.
        """
        message = {"schema": self.schema, "payload": value}
        self.producer.produce(self.kafka_topic, key=key, value=json.dumps(message))

    def flush(self):
        """Flushes the Kafka producer queue."""
        self.producer.flush()

    def process_block(self, block: BlockData):
        """
        Processes a block, extracts swap events, and sends them to Kafka.

        Args:
            block (BlockData): Ethereum block data.
        """
        block_number = block.number
        block_time = block.timestamp * 1000  # Convert to milliseconds
        event_filter = self.contract.events.Swap.create_filter(
            from_block=block_number, to_block=block_number
        )
        events = event_filter.get_all_entries()

        for index, event in enumerate(events):
            transform_fn = self.transformations.get(self.config_name)
            if transform_fn:
                key = json.dumps({"block_number": block_number, "index": index})
                data = transform_fn(
                    block_number, block_time, str(self.pool_address), index, event
                )
                self.send_message(key, data)


def to_uniswap_swap(
    block_number: int, block_time: int, contract_address: str, index: int, event
) -> dict:
    """
    Transforms a Web3 event into a Uniswap swap as a structured dictionary.

    Args:
        block_number (int): Block number of the event.
        block_time (int): Timestamp of the block in milliseconds.
        contract_address (str): Address of the contract emitting the event.
        index (int): Index of the event within the block.
        event: Raw event data.

    Returns:
        dict: Transformed event data.
    """
    event_args = event["args"]
    return {
        "block_number": block_number,
        "block_time": block_time,
        "contract_address": contract_address,
        "tx_hash": (
            event.get("transactionHash", b"").hex()
            if "transactionHash" in event
            else ""
        ),
        "index": index,
        "sender": event_args.get("sender", ""),
        "recipient": event_args.get("recipient", ""),
        "amount0": int(event_args.get("amount0", 0)),
        "amount1": int(event_args.get("amount1", 0)),
        "sqrt_price_x96": float(event_args.get("sqrtPriceX96", 0)),
        "liquidity": int(event_args.get("liquidity", 0)),
        "tick": int(event_args.get("tick", 0)),
    }
