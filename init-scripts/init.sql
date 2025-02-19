CREATE SCHEMA IF NOT EXISTS uniswap;

CREATE TABLE IF NOT EXISTS uniswap.swap (
    block_number BIGINT,
    block_time TIMESTAMP,
    contract_address TEXT,
    tx_hash TEXT,
    index BIGINT,
    sender TEXT,
    recipient TEXT,
    amount0 BIGINT,
    amount1 BIGINT,
    sqrt_price_x96 NUMERIC,
    liquidity BIGINT,
    tick BIGINT
);