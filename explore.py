from src.client import KalshiClient
import json

def main():
    client = KalshiClient()
    params = {"limit" : 2,
              "status": "open",
             }
    data = client.get("/events",params)
    print(json.dumps(data,indent=2))

if __name__ == "__main__":
    main()