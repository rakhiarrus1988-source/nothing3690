import os
import json
from google.colab import drive

def setup_environment():
    # 1. Mount Google Drive
    print("🔄 Mounting Google Drive to save credentials...")
    drive.mount('/content/drive')
    
    # 2. Create permanent folder in Drive
    DATA_DIR = "/content/drive/MyDrive/TG_TeraBox_Data"
    os.makedirs(DATA_DIR, exist_ok=True)
    
    config_path = os.path.join(DATA_DIR, "config.json")
    session_path = os.path.join(DATA_DIR, "tg_session")
    
    config_data = {}
    
    # 3. Load existing config or ask for new input
    if os.path.exists(config_path):
        print("💾 Found existing credentials in Google Drive. Loading...")
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    else:
        print("\n📝 No credentials found. Please enter them below:")
        config_data['api_id'] = int(input("Enter Telegram API ID (from my.telegram.org): ").strip())
        config_data['api_hash'] = input("Enter Telegram API Hash: ").strip())
        config_data['terabox_ndus'] = input("Enter TeraBox 'ndus' Cookie value: ").strip()
        
        # Save to Drive instantly
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        print("✅ Credentials saved securely to your Google Drive!")
        
    return config_data, session_path
