#!/bin/bash

# Wait for Kafka Connect to be ready
echo "Waiting for Kafka Connect to be ready..."
while ! curl -s http://kafka-connect:8083/connectors; do
    sleep 5
done
echo "Kafka Connect is ready."


# Register all Kafka Connect sink connectors
for file in ingester/kafka-sink-configs/*.json; do
    echo "Registering Kafka Sink Connector from $file..."
    curl -X POST -H "Content-Type: application/json" --data @"$file" http://kafka-connect:8083/connectors || echo "Connector from $file already exists."
done

# Run the Uniswap ingester script in the foreground
echo "Running the Uniswap ingester script... \n"
exec python3 -u ingester/ingest.py
