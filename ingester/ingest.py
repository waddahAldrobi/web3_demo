import time
import logging
from datetime import datetime, timezone
from State import State
from Pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

STATE_FILE = "state.json"
CONFIG = "uniswap_swap"


def main():
    """Main loop to process new Ethereum blocks and send events to Kafka."""
    try:
        pipeline = Pipeline(CONFIG)
        state_manager = State(STATE_FILE)

        # Get the last processed block or start from the latest block
        last_processed_block = state_manager.get_last_processed_block(pipeline.web3)
        logging.info(f"Starting from block: {last_processed_block}")

        while True:
            try:
                current_block = pipeline.web3.eth.block_number

                if current_block > last_processed_block:
                    # Process each new block in sequence
                    for block_number in range(
                        last_processed_block + 1, current_block + 1
                    ):
                        try:
                            block = pipeline.web3.eth.get_block(block_number)
                            block_time = datetime.fromtimestamp(
                                block.timestamp, timezone.utc
                            ).isoformat()

                            logging.info(
                                f"Processing block {block.number} - Block Time: {block_time}"
                            )

                            pipeline.process_block(block)
                            state_manager.update_last_processed_block(block_number)

                        except Exception as e:
                            logging.error(
                                f"Error processing block {block_number}: {e}",
                                exc_info=True,
                            )

                # Ensure all messages are sent to Kafka before the next poll
                pipeline.flush()

            except Exception as e:
                logging.error(f"Error in main loop: {e}", exc_info=True)

            # Sleep before checking for new blocks
            time.sleep(pipeline.poll_interval)

    except Exception as e:
        logging.critical(f"Fatal error during initialization: {e}", exc_info=True)


if __name__ == "__main__":
    main()
