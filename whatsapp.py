import os, argparse, requests, configparser, json

configdir = os.path.expanduser('~/.whatsapp_automation')
version = "0.1 -- 2025 By Josjuar Lister"
API_URL = ""  # Change if running API elsewhere

def configure() -> configparser.ConfigParser:
    #Create directory to store user data
    if(not os.path.exists(f"{configdir}")):
        print(f"Creating directory {configdir}")
        os.makedirs(configdir)

    config = configparser.ConfigParser()

    if(not os.path.exists(f"{configdir}/config.cfg")):
        default_config = f"""[Settings]
                            chrome_user_data_dir={configdir}/chrome-data
                            whatsapp_url=https://web.whatsapp.com
                            host=127.0.0.1
                            port=5000
                            log_path={configdir}/whatsapp_web_service.log"""
        # Create configuration file
        with open(f"{configdir}/config.cfg", 'w') as configfile:
            configfile.write(default_config)
        config.read_string(default_config)
    else:
        # Read configuration from cfg file
        config.read(f"{configdir}/config.cfg")
    return config

def api_call(endpoint, params):
    global API_URL
    r = None
    try:
        r = requests.get(f"{API_URL}/{endpoint}", params=params)
    except Exception as e:
        print(f"An error occoured: {e}")
        return None
    response = r.json()
    if(response["status"] != "success"):
        print("The WhatsApp Web service experienced a problem")
        exit(1)
    return response

def read_chat(chat_name, n_read):
    response = api_call("read", {"chat_name": chat_name, "n_read": n_read})
    print(f"🔔 Messages from {chat_name}:")
    for msg in response["messages"]:
        print(f"📨 {msg}")

def get_latest_unread_messages():
    chats = api_call("last", [])

    print(f"✅ Found {chats['chats found']} Chat's with unread messages")
    if chats["chats found"] != 0:
        print("🔔 Unread Chats:")
        for c in chats["chats"]:
            print(f"📨 {c['message_count']} Messages from: \"{c['chat_title']}\"")

def send_message(chat_name, message):
    response = api_call("send", {"chat_name": chat_name, "message": message})
    print(f"✅ Message sent to {response['chat']}")

def run(args):
    # Read chat messages
    if args.read:
        chat_name = input("Which chat do you want to read? -- ") if args.read is True else args.read
        read_chat(chat_name, args.number)
        exit(0)
   
    # See unread messages
    if args.last:
        get_latest_unread_messages()
        exit(0)
    
    if args.send:
        if args.to is None:
            to = input("Who would you like to send that to? -- ")
        else:
            to = args.to
        send_message(to, args.send)
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A CLI client for WhatsApp Web automation")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parser.add_argument("--send", help="Message to send")
    parser.add_argument("--to", help="Contact name")
    parser.add_argument("--last", help="Show latest unread messages", action="store_true")
    parser.add_argument("--read", help="Read messages from a specified chat", nargs="?", const=True)
    parser.add_argument("--number", "-n", help="How many messages to display from a chat", type=int, default=1)
    args = parser.parse_args()

    config = configure()
    API_URL = f"http://{config.get('Settings', 'host')}:{config.get('Settings', 'port')}/"

    try:
        requests.get(f"{API_URL}/version")
        run(args)
    except:
        print("Please start the web service API")


    # If no arguments are passed
    to = input("Enter the contact name: ")
    message = input("Enter your message: ")
    send_message(to, message)

