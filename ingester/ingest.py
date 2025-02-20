import time
from web3 import Web3
from web3.types import BlockData
from confluent_kafka import Producer
from datetime import datetime, timezone
from State import State
from Pipeline import Pipeline


STATE_FILE = "state.json"
CONFIG = "uniswap_swap"


def main():
    pipeline = Pipeline(CONFIG)
    state_manager = State(STATE_FILE)
    last_processed_block = state_manager.get_last_processed_block(pipeline.web3)
    print(f"Starting from block: {last_processed_block}")

    while True:
        current_block = pipeline.web3.eth.block_number
        if current_block > last_processed_block:
            for block_number in range(last_processed_block + 1, current_block + 1):
                block = pipeline.web3.eth.get_block(block_number)
                print(
                    f"Processing block: {block.number} - Block Time: {datetime.fromtimestamp(block.timestamp, timezone.utc).isoformat()}"
                )
                pipeline.process_block(block)
                state_manager.update_last_processed_block(block_number)

        pipeline.flush()
        time.sleep(pipeline.poll_interval)


if __name__ == "__main__":
    main()
