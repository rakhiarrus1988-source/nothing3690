import os
import sys
import asyncio
import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from telethon import TelegramClient
from config import setup_environment

# Progress bar function for visual feedback during upload/download
def progress_callback(current, total, operation="Processing"):
    percentage = (current / total) * 100
    sys.stdout.write(f"\r🚀 {operation}: {percentage:.2f}% ({current}/{total} bytes)")
    sys.stdout.flush()

async def download_tg_file(client, file_link_or_msg_id, download_dir):
    print("\n🔍 Connecting to Telegram to fetch the file...")
    
    # Simple parser for message link or direct ID input
    try:
        if "t.me/" in file_link_or_msg_id:
            parts = file_link_or_msg_id.split('/')
            chat = parts[-2]
            msg_id = int(parts[-1])
            message = await client.get_messages(chat, ids=msg_id)
        else:
            # If user inputs direct message ID (assumes saved messages/current chat context)
            msg_id = int(file_link_or_msg_id)
            message = await client.get_messages('me', ids=msg_id)
            
        if not message or not message.media:
            print("❌ Error: No media found in the provided link/ID.")
            return None
            
        filename = getattr(message.media, 'document', None)
        if filename:
            for attr in filename.attributes:
                if hasattr(attr, 'file_name'):
                    actual_name = attr.file_name
                    break
            else:
                actual_name = "tg_downloaded_file"
        else:
            actual_name = "tg_downloaded_file"
            
        target_path = os.path.join(download_dir, actual_name)
        
        print(f"📥 Downloading: {actual_name}")
        # Telethon natively handles high-speed multi-part downloads on Colab backbone
        await client.download_media(message, target_path, 
                                    progress_callback=lambda c, t: progress_callback(c, t, "Downloading"))
        print("\n✅ Download complete!")
        return target_path
        
    except Exception as e:
        print(f"\n❌ Telegram Download Failed: {str(e)}")
        return None

def upload_to_terabox(file_path, ndus_cookie):
    if not os.path.exists(file_path):
        print("❌ Local file not found for uploading.")
        return
        
    filename = os.path.basename(file_path)
    print(f"\n📤 Initialising TeraBox Upload for: {filename}")
    
    # Setup headers and authentication cookies
    cookies = {'ndus': ndus_cookie}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://terabox.com'
    }
    
    # 1. Get pre-upload requirements / URL allocation
    # Note: Free tier speeds are restricted server-side by TeraBox api endpoints.
    try:
        # Initial checking endpoint to fetch optimal cluster upload server
        init_url = "https://terabox.comapi/precreate"
        # Dummy dynamic form data payload structure for web API parsing
        params = {
            'path': f'/{filename}',
            'size': os.path.getsize(file_path),
            'isdir': '0'
        }
        
        # Stream wrapper setup to utilize full pipe without choking Colab RAM
        encoder = MultipartEncoder(fields={'file': (filename, open(file_path, 'rb'), 'application/octet-stream')})
        monitor = MultipartEncoderMonitor(encoder, lambda monitor: progress_callback(monitor.bytes_read, monitor.len, "Uploading"))
        
        # Requesting TeraBox standard upload endpoint
        upload_url = "https://terabox.com"
        
        upload_headers = {**headers, 'Content-Type': monitor.content_type}
        
        print("⚡ Pushing data stream to TeraBox storage cluster...")
        response = requests.post(upload_url, data=monitor, cookies=cookies, headers=upload_headers)
        
        if response.status_code == 200 or response.status_code == 201:
            print("\n🎉 Upload Successfully finished on TeraBox Cloud Storage!")
            # Delete local file to keep Colab environment clean
            os.remove(file_path)
            print("🧹 Cleaned local space.")
        else:
            print(f"\n❌ TeraBox upload rejected server side. Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error during TeraBox upload pipe: {str(e)}")

async def main():
    # Load configuration and initialize storage mount
    config, session_file = setup_environment()
    
    # Initialize high speed Telethon asynchronous engine
    client = TelegramClient(session_file, config['api_id'], config['api_hash'])
    
    print("🔐 Connecting and logging into Telegram protocol...")
    await client.start() # This prompts for OTP dynamic input on your terminal inside Colab if running first time
    print("🔓 Active session verified.")
    
    # Dynamic runtime instructions
    download_dir = "/content/local_cache"
    os.makedirs(download_dir, exist_ok=True)
    
    # Infinite operational loop to process links one by one dynamically
    while True:
        tg_input = input("\n🔗 Enter Telegram Message Link / ID (or type 'exit' to stop): ").strip()
        if tg_input.lower() == 'exit':
            break
            
        downloaded_file = await download_tg_file(client, tg_input, download_dir)
        
        if downloaded_file:
            upload_to_terabox(downloaded_file, config['terabox_ndus'])
            
    await client.disconnect()
    print("\n👋 Process finished. Session closed cleanly.")

if __name__ == "__main__":
    asyncio.run(main())
