# smoke_test.py
"""
Live smoke test against Kalshi demo API.
This actually hits the network — it's not a unit test.
Run with: uv run python smoke_test.py
"""
from src.client import KalshiClient


def main():
    print("Initializing client...")
    client = KalshiClient()
    
    print(f"Hitting {client.base_url}/portfolio/balance ...")
    balance = client.get("/portfolio/balance")
    
    print("Success! Response:")
    print(balance)


if __name__ == "__main__":
    main()