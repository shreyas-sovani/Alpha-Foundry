#!/usr/bin/env python3
"""Quick MCP endpoint test"""
import asyncio
import httpx

async def test_mcp():
    base_url = "https://mcp.blockscout.com/mcp"
    chain_id = 11155111  # Sepolia
    
    print(f"Testing MCP endpoint: {base_url}")
    print(f"Chain ID: {chain_id}")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Get latest block
        try:
            print("\n1. Testing get_latest_block...")
            response = await client.post(
                f"{base_url}/get_latest_block",
                json={"chain_id": chain_id}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Try without /mcp suffix
        try:
            print("\n2. Testing without /mcp suffix...")
            response = await client.post(
                "https://mcp.blockscout.com/get_latest_block",
                json={"chain_id": chain_id}
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Check root endpoint
        try:
            print("\n3. Checking root endpoint...")
            response = await client.get("https://mcp.blockscout.com")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp())
