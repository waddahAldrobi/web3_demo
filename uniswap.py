import json
import os
import time
from web3 import Web3
from web3.types import BlockData
from confluent_kafka import Producer
from datetime import datetime, timezone

# Ethereum RPC endpoint
rpc_url = "https://eth-mainnet.g.alchemy.com/v2/4OuWznL5wxq_yl-ujF7Cybb4iTfve1bG"
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Check connection
if w3.is_connected():
    print("✅ Connected to Ethereum!")
else:
    print("❌ Connection failed.")
    exit(1)

POOL_ADDRESS = Web3.to_checksum_address("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640")

# ABI for the Swap event
abi = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "sender",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "recipient",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "int256",
                "name": "amount0",
                "type": "int256",
            },
            {
                "indexed": False,
                "internalType": "int256",
                "name": "amount1",
                "type": "int256",
            },
            {
                "indexed": False,
                "internalType": "uint160",
                "name": "sqrtPriceX96",
                "type": "uint160",
            },
            {
                "indexed": False,
                "internalType": "uint128",
                "name": "liquidity",
                "type": "uint128",
            },
            {
                "indexed": False,
                "internalType": "int24",
                "name": "tick",
                "type": "int24",
            },
        ],
        "name": "Swap",
        "type": "event",
    }
]

contract = w3.eth.contract(address=POOL_ADDRESS, abi=abi)
state_file = "state.json"

# Kafka configuration
TOPIC = "uniswap-topic"
KAFKA_BROKER = "localhost:29092"
producer_config = {"bootstrap.servers": KAFKA_BROKER}
producer = Producer(producer_config)


def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Message delivery failed: {err}")
    else:
        print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")


def send_message(key, value):
    message = {
        "schema": {
            "type": "struct",
            "fields": [
                {"type": "int64", "optional": False, "field": "block_number"},
                {"type": "int64", "optional": False, "field": "block_time"},
                {"type": "string", "optional": False, "field": "contract_address"},
                {"type": "string", "optional": False, "field": "tx_hash"},
                {"type": "int64", "optional": False, "field": "index"},
                {"type": "string", "optional": False, "field": "sender"},
                {"type": "string", "optional": False, "field": "recipient"},
                {"type": "int64", "optional": True, "field": "amount0"},
                {"type": "int64", "optional": True, "field": "amount1"},
                {"type": "double", "optional": True, "field": "sqrt_price_x96"},
                {"type": "int64", "optional": True, "field": "liquidity"},
                {"type": "int64", "optional": True, "field": "tick"},
            ],
            "optional": False,
            "name": "uniswap_swap",
        },
        "payload": value,
    }

    producer.produce(
        TOPIC, key=str(key), value=json.dumps(message), callback=delivery_report
    )


def load_state():
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(state_file, "w") as f:
        json.dump(state, f)


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
            "contract_address": str(POOL_ADDRESS),
            "tx_hash": (
                event.get("transactionHash", "").hex()
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

        # print(data)
        send_message(key=index, value=data)


def main():
    state = load_state()
    last_processed_block = state.get("last_processed_block", w3.eth.block_number)
    save_state({"last_processed_block": last_processed_block})
    print(f"Starting from block: {last_processed_block}")

    while True:
        current_block = w3.eth.block_number
        if current_block > last_processed_block:
            for block_number in range(last_processed_block + 1, current_block + 1):
                block = w3.eth.get_block(block_number)
                print(f"Processing block: {block.number}")
                print(
                    f"Block time: {datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat()}"
                )

                process_block(block)
                last_processed_block = block_number
                save_state({"last_processed_block": last_processed_block})

        producer.flush()
        time.sleep(10)


if __name__ == "__main__":
    main()
