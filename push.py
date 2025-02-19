from confluent_kafka import Producer
import json
import time

# Kafka configuration
TOPIC = "uniswap-topic"
KAFKA_BROKER = "localhost:29092"  # External listener

# Configure Kafka producer
producer_config = {
    'bootstrap.servers': KAFKA_BROKER
}
producer = Producer(producer_config)

def delivery_report(err, msg):
    """Delivery report callback called on message success/failure."""
    if err is not None:
        print(f"❌ Message delivery failed: {err}")
    else:
        print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")

def send_message(key, value):
    """Send a message with an explicit schema for Kafka Connect."""
    message = {
        "schema": {
            "type": "struct",
            "fields": [
                {"type": "int32", "optional": False, "field": "id"},
                {"type": "string", "optional": False, "field": "message"}
            ],
            "optional": False,
            "name": "uniswap_message"
        },
        "payload": value
    }

    producer.produce(TOPIC, key=str(key), value=json.dumps(message), callback=delivery_report)

if __name__ == "__main__":
    for i in range(5):  # Send 5 test messages
        send_message(key=i, value={"id": i, "message": f"Hello Kafka {i}"})
        time.sleep(1)  # Small delay to simulate real-world usage

    producer.flush()  # Ensure all messages are sent before exiting
