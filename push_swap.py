from confluent_kafka import Producer
import json
import time
import base64

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
                {"type": "string", "optional": False, "field": "contract_address"},
                {"type": "string", "optional": False, "field": "tx_hash"},
                {"type": "int64", "optional": False, "field": "index"},
                # {"type": "timestamp", "optional": False, "field": "block_time"},
                {"type": "int64", "optional": False, "field": "block_number"},
                {"type": "string", "optional": False, "field": "sender"},
                {"type": "string", "optional": False, "field": "recipient"},
                {"type": "int64", "optional": False, "field": "amount0"},
                {"type": "int64", "optional": False, "field": "amount1"},
                {"type": "double", "optional": False, "field": "sqrt_price_x96"},
                {"type": "int64", "optional": False, "field": "liquidity"},
                {"type": "int64", "optional": False, "field": "tick"}
            ],
            "optional": False,
            "name": "uniswap_swap"
        },
        "payload": value
    }

    producer.produce(TOPIC, key=str(key), value=json.dumps(message), callback=delivery_report)

if __name__ == "__main__":
    for i in range(3):  # Send 3 test messages
        data = {
            "contract_address": "0xae6373a902c23123bEF1E3c0a07A538dE0Df118D",
            "tx_hash": "0xae6373a902c23123bEF1E3c0a07A538dE0Df118D",
            "index": i,
            "block_number": 12345678 + i,
            "sender": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
            "recipient": "0xae6373a902c23123bEF1E3c0a07A538dE0Df118D",
            "amount0": 1000 * (i + 1),
            "amount1": 2000 * (i + 1),
            "sqrt_price_x96": 1.23456789,
            "liquidity": 500000 + i,
            "tick": 100 + i
        }
        send_message(key=i, value=data)
        time.sleep(1) 

    producer.flush()  