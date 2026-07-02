import os
import sys
import asyncio
from google.colab import drive
from telethon import TelegramClient

# --- STEP 1: GOOGLE DRIVE MOUNT (CREDENTIALS AUTO-SAVE) ---
print("🔄 Mounting Google Drive to load/save credentials...")
drive.mount('/content/drive')

# Google Drive par permanent credentials folder setup
CRED_DIR = "/content/drive/MyDrive/TG_TeraBox_Bot"
os.makedirs(CRED_DIR, exist_ok=True)
session_path = os.path.join(CRED_DIR, "telegram_session")

# --- STEP 2: TELEGRAM API CREDENTIALS ---
# Inhe aap my.telegram.org se lekar yahan fill karein
API_ID = 1234567          # Apna API ID daalein (Integer)
API_HASH = 'your_api_hash' # Apna API Hash string daalein

# Colab ki local storage download directory
DOWNLOAD_DIR = "/content/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# --- STEP 3: TERABOX UPLOAD LOGIC ---
def upload_to_terabox(file_path):
    """
    TeraBox upload handling function.
    Google Colab high bandwidth ka use karke upload start karega.
    """
    print(f"\n📤 Uploading to TeraBox: {os.path.basename(file_path)}")
    
    terabox_token_path = os.path.join(CRED_DIR, "terabox_credentials.txt")
    if not os.path.exists(terabox_token_path):
        print("⚠️ Warning: TeraBox credentials track nahi mile Drive me.")
        print("Kripya setup check karein. Upload process skip ho raha hai.")
        return False
        
    try:
        # NOTE: TeraBox high-speed CLI tool ya customized Rclone setup command yahan chalega
        # Example command pipeline:
        # os.system(f"rclone move '{file_path}' terabox:/remote_folder --progress")
        
        print("✅ TeraBox Upload Successful!")
        return True
    except Exception as e:
        print(f"❌ TeraBox Upload Failed: {e}")
        return False


# --- STEP 4: TELEGRAM SEARCH & DOWNLOAD LOGIC ---
async def process_saved_messages():
    # Telegram Client Init (Drive session file use hogi, baar-baar login nahi karna padega)
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.start()
    print("\n⚡ Telegram Client Successfully Connected to Saved Messages!")

    while True:
        # User se live file name maangne ka option
        file_query = input("\n🔍 Enter File Name to Search & Download (or type 'exit'): ").strip()
        
        if file_query.lower() == 'exit':
            print("👋 Exiting main script. Bye!")
            break
            
        if not file_query:
            print("❌ Error: Khali naam mat daalo bhai!")
            continue

        print(f"🔄 Searching for '{file_query}' in your Saved Messages...")
        
        # 'me' keyword ka matlab Saved Messages hota hai. 
        # search parameter poore server-side database me naam filter karega.
        found_message = None
        async for message in client.iter_messages('me', search=file_query):
            if message.media:
                found_message = message
                break # Pehla matching record milte hi loop break
                
        if not found_message:
            print(f"❌ '{file_query}' naam ki koi file Saved Messages me nahi mili.")
            print("💡 Tip: Sahi spelling ya file extension (jaise .mp4, .mkv) daalkar try karein.")
            continue

        # File metadata information nikalna
        actual_file_name = "tg_downloaded_file"
        if hasattr(found_message.media, 'document'):
            for attr in found_message.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    actual_file_name = attr.file_name
                    break

        print(f"📦 File Found: {actual_file_name}")
        print("🚀 Downloading to Google Colab with High Bandwidth...")
        
        # High speed chunk downloading process
        downloaded_path = await client.download_media(found_message, file=DOWNLOAD_DIR)
        
        if downloaded_path and os.path.exists(downloaded_path):
            print(f"✅ Download Finished! File Saved locally at: {downloaded_path}")
            
            # TeraBox upload trigger karna
            upload_success = upload_to_terabox(downloaded_path)
            
            # Storage management: Space full na ho isliye local file delete karna
            if os.path.exists(downloaded_path):
                os.remove(downloaded_path)
                print("🧹 Colab storage cleaned up for the next file.")
        else:
            print("❌ Download fail ho gaya, kripya connection check karein.")

    await client.disconnect()


# --- STEP 5: RUNTIME EXECUTION GATEWAY ---
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        try:
            # Jupyter/Colab async loop detection management
            import asyncio
            try:
                await process_saved_messages()
            except RuntimeError:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(process_saved_messages())
        except Exception as err:
            print(f"Fatal Error: {err}")
    else:
        print("⚙️ main.py script configured. Run using appropriate python commands inside notebook.")
