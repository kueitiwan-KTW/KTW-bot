from gmail_helper import GmailHelper
from google_services import GoogleServices
from dotenv import load_dotenv
import os

load_dotenv()

def debug_mismatch():
    print("Initializing...")
    services = GoogleServices()
    helper = GmailHelper(services)
    
    order_id = "609558"
    print(f"Testing Deep Scan match for: {order_id}")
    
    # Simulate fetching the specific problematic email
    # I need to find its ID. I'll search for 1675664593 first.
    print("Fetching email '1675664593' to inspect content...")
    results = helper.service.users().messages().list(userId='me', q='"1675664593"', maxResults=1).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("Could not find the target email '1675664593' to test against.")
        return

    msg_id = messages[0]['id']
    m = helper.service.users().messages().get(userId='me', id=msg_id).execute() # Full format
    
    headers = m['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    snippet = m.get('snippet', '')
    
    print(f"Subject: {subject}")
    print(f"Snippet: {snippet}")
    
    print("-" * 20)
    print(f"Checking substring match: '{order_id}' in Subject?")
    print(f"Result: {order_id in subject}")
    
    print(f"Checking substring match: '{order_id}' in Snippet?")
    print(f"Result: {order_id in snippet}")

if __name__ == "__main__":
    debug_mismatch()
