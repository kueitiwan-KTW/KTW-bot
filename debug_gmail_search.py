from gmail_helper import GmailHelper
from google_services import GoogleServices
from dotenv import load_dotenv
import os

load_dotenv()

def debug_search():
    print("Initializing Google Services...")
    services = GoogleServices()
    helper = GmailHelper(services)
    
    # 3. List recent emails to see patterns
    print(f"\n🔎 Listing recent emails to debug patterns...")
    try:
        messages = helper.service.users().messages().list(userId='me', maxResults=10).execute().get('messages', [])
        for msg in messages:
            m = helper.service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = m['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            print(f" - {subject}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_search()
