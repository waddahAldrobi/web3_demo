from kafka import KafkaProducer
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Kafka broker address
KAFKA_BROKER = "localhost:9092"  # If using Docker network, try "kafka:9092"
TOPIC_NAME = "uniswap-topic"

# Create Kafka producer with error handling
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        retries=5  # Retries if Kafka is temporarily unavailable
    )
    logging.info("Kafka Producer connected successfully.")
except Exception as e:
    logging.error(f"Failed to connect to Kafka: {e}")
    exit(1)

def send_message(id, message):
    """Send message to Kafka topic with logging."""
    data = {
        "schema": {
            "type": "struct",
            "fields": [
                {"type": "int32", "optional": False, "field": "id"},
                {"type": "string", "optional": False, "field": "message"}
            ],
            "optional": False,
            "name": "uniswap_message"
        },
        "payload": {
            "id": id,
            "message": message
        }
    }

    try:
        future = producer.send(TOPIC_NAME, value=data)
        result = future.get(timeout=10)  # Wait for confirmation
        logging.info(f"Message sent successfully: {data}")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

# Test sending messages
send_message(1, "First message")
send_message(2, "Second message")

producer.flush()
producer.close()
