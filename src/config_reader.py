import json

def read_config():
    """Reads the configuration file and returns the settings."""
    with open('config.json', 'r') as f:
        return json.load(f)

if __name__ == '__main__':
    config = read_config()
    print("Configuration loaded:")
    for key, value in config.items():
        print(f"  {key}: {value}")
