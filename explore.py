from src.client import KalshiClient
import json

def main():
    client = KalshiClient()
    params = {"limit" : 5,
              "status": "open",
              "with_nested_markets": True
             }
    data = client.get("/events",params)
    print(json.dumps(data,indent=2))

if __name__ == "__main__":
    main()