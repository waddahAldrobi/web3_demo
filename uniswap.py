from web3 import Web3

# Replace with your Ethereum RPC endpoint
rpc_url = "https://eth-mainnet.g.alchemy.com/v2/4OuWznL5wxq_yl-ujF7Cybb4iTfve1bG"  # Example: Infura, Alchemy, or local node
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Check connection
if w3.is_connected():
    print("✅ Connected to Ethereum!")
else:
    print("❌ Connection failed.")


POOL_ADDRESS = Web3.to_checksum_address('0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')

# ABI for the Swap event
abi = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "recipient", "type": "address"},
            {"indexed": False, "internalType": "int256", "name": "amount0", "type": "int256"},
            {"indexed": False, "internalType": "int256", "name": "amount1", "type": "int256"},
            {"indexed": False, "internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"indexed": False, "internalType": "int24", "name": "tick", "type": "int24"}
        ],
        "name": "Swap",
        "type": "event"
    }
]

# Use the checksum address in your contract initialization
contract = w3.eth.contract(address=POOL_ADDRESS, abi=abi)

from_block = 13558910
to_block = 13558912

# Create filter for Swap events in block range
event_filter = contract.events.Swap.create_filter(from_block=from_block, to_block=to_block)

# Fetch all matching events
events = event_filter.get_all_entries()



for event in events:
    print(event)
    # print(f"contract_address: {event['args']['contract_address']}")
    # print(f"tx_hash: {event['args']['tx_hash']}")
    # print(f"index: {event['args']['index']}")
    # print(f"block_time: {event['args']['block_time']}")
    # print(f"block_number: {event['args']['block_number']}")
    print(f"Sender: {event['args']['sender']}, Recipient: {event['args']['recipient']}")
    print(f"Amount0: {event['args']['amount0']}, Amount1: {event['args']['amount1']}")
    print(f"Liquidity: {event['args']['liquidity']}, Tick: {event['args']['tick']}")
    print("="*50)
    print('\n')




