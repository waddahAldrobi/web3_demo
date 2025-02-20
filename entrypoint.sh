#!/bin/bash

# Wait for Kafka Connect to be ready
echo "Waiting for Kafka Connect to be ready..."
while ! curl -s http://kafka-connect:8083/connectors; do
    sleep 5
done
echo "Kafka Connect is ready."


# Register the Kafka Connect sink connector
echo "Registering PostgreSQL Sink Connector...\n"
curl -X POST -H "Content-Type: application/json" --data @postgres-sink.json http://kafka-connect:8083/connectors || echo "Connector already exists. \n"

# Run the Uniswap ingester script in the foreground
echo "Running the Uniswap ingester script... \n"
exec python3 -u ingester/uniswap.py
