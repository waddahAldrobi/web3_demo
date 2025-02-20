import json
import os
import time
from web3 import Web3
from web3.types import BlockData
from confluent_kafka import Producer
from datetime import datetime, timezone
from State import State
from Pipeline import Pipeline


KAFKA_BROKER = "localhost:29092"
STATE_FILE = "state.json"

current_dir = os.path.dirname(os.path.abspath(__file__))
pipeline = Pipeline(os.path.join(current_dir, "configs/uniswap_swap.json"))

rpc_url = pipeline.rpc
pool_address = Web3.to_checksum_address(pipeline.pool_address)
topic = pipeline.kafka_topic
poll_interval = pipeline.poll_interval
schema = pipeline.schema
abi = pipeline.abi

# Connect to Ethereum
w3 = Web3(Web3.HTTPProvider(rpc_url))
if w3.is_connected():
    print("✅ Connected to Ethereum!")
else:
    print("❌ Connection failed.")
    exit(1)

contract = w3.eth.contract(address=pool_address, abi=abi)
producer = Producer({"bootstrap.servers": KAFKA_BROKER})


def send_message(key, value):
    message = {"schema": schema, "payload": value}
    producer.produce(topic, key=str(key), value=json.dumps(message))


def process_block(block: BlockData):
    block_number = block.number
    block_time = block.timestamp * 1000  # Convert to milliseconds
    event_filter = contract.events.Swap.create_filter(
        from_block=block_number, to_block=block_number
    )
    events = event_filter.get_all_entries()

    for index, event in enumerate(events):
        event_args = event["args"]
        data = {
            "block_number": block_number,
            "block_time": block_time,
            "contract_address": str(pool_address),
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
        send_message(key=index, value=data)


def main():
    state_manager = State(STATE_FILE)
    last_processed_block = state_manager.get_last_processed_block(w3)
    print(f"Starting from block: {last_processed_block}")

    while True:
        current_block = w3.eth.block_number
        if current_block > last_processed_block:
            for block_number in range(last_processed_block + 1, current_block + 1):
                block = w3.eth.get_block(block_number)
                print(
                    f"Processing block: {block.number} - Block Time: {datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat()}"
                )
                process_block(block)
                state_manager.update_last_processed_block(block_number)

        producer.flush()
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
