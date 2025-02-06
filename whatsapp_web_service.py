
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, request, jsonify
from pyzbar.pyzbar import decode
from PIL import Image
import time, configparser, os, qrcode


configdir = os.path.expanduser('~/.whatsapp_automation')
version = "whatsapp_web_service 0.1 -- 2025 By Josjuar Lister"

driver: webdriver.Chrome = None
app = Flask(__name__)
logpath = ""
logfile = None
authenticated = False

def logf(string):
    log = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {string}"
    print(log)
    logfile.write(log + '\n')

def configure() -> configparser.ConfigParser:
    #Create directory to store user data
    if(not os.path.exists(f"{configdir}")):
        logf("Creating directory /var/local/whatsapp_automation")
        os.makedirs(os.path.expanduser('~/.whatsapp_automation'))

    config = configparser.ConfigParser()

    if(not os.path.exists(f"{configdir}/config.cfg")):
        default_config = f"""[Settings]
                            chrome_user_data_dir={configdir}/chrome-data
                            whatsapp_url=https://web.whatsapp.com
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

def generate_qr_code(image_path):
    img = Image.open(image_path)
    qr_code = decode(img)[0]
    data = qr_code.data.decode("utf-8")
    qr = qrcode.QRCode()
    qr.add_data(data)
    qr.make()
    qr.print_ascii()  # Generates ASCII version of QR code

def getdriver(config: configparser.ConfigParser, headless=True):
    global authenticated
    # Extract configuration values
    chrome_user_data_dir = config.get('Settings', 'chrome_user_data_dir', fallback=f"{configdir}/chrome-data")

    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={chrome_user_data_dir}")  # Keeps session alive
    if (headless):
        options.add_argument("--headless=new")  # New headless mode
        options.add_argument("--disable-gpu")  # Fixes rendering issues
        options.add_argument("--window-size=1920,1080")  # Ensures proper page loading
        options.add_argument("--no-sandbox")  # Prevents sandboxing issues
        options.add_argument("--enable-webgl")  # Ensures WebRTC loads properly
        options.add_argument("--use-fake-ui-for-media-stream")  # Stops camera popups

        # Spoof user-agent to appear like a normal Chrome browser
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
    
    driver = webdriver.Chrome(options=options)
    whatsapp_url = config.get('Settings', 'whatsapp_url', fallback='https://web.whatsapp.com/')

    # Open WhatsApp Web
    driver.get(f"{whatsapp_url}")
    logf("🔗 Opening WhatsApp Web...")

    try:
        search_box = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )
        logf("✅ Logged in!")
        authenticated = True
    except:
        print("Trying to find QR...")
        try:
            qr_canvas = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "canvas"))
            )
            logf("❌ Not Logged in! QR code detected.")
            qr_canvas.screenshot(f"{configdir}/qr_code.png")
            logf(f"📸 QR code screenshot saved to {configdir}/qr_code.png")

            """Generates an ASCII QR code from text."""
            try:
                print(generate_qr_code(f"{configdir}/qr_code.png"))

            except Exception as e:
                print(e)
        except:
            logf("❌ Not Logged in! QR code not detected.")

    return driver

def scan_qr():
    return jsonify({"status": "Not Authenticated", 
                    "Action": "Please scan the QR code from your Whatsapp app",
                    "qr_path": f"{configdir}/qr_code.png"}), 403

def get_chat(chat_name):
    if not chat_name:
        return jsonify({"status": "failure", "error": "Missing chat_name"}), 400
    try:
        search_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )
    except:
        logf("❌ failed! Search box not found.")
        driver.quit()
        return        
            
    # Search for the contact
    logf(f"🔍 Searching for {chat_name}...")
    search_box.click()
    search_box.clear()
    search_box.send_keys(chat_name)
    time.sleep(1)
    search_box.send_keys(Keys.ENTER)
    time.sleep(1)

def clear_search():
  try:
    search_icon = WebDriverWait(driver, 30).until(
      EC.presence_of_element_located((By.XPATH, "//span[@data-icon='search']"))
    )
    search_icon.click()
    logf("🔍 Search box cleared.")
  except Exception as e:
    logf(f"❌ Failed to clear search box: {e}")

@app.route('/send', methods=['GET'])
def send():
    if not authenticated:
        return scan_qr()
    global driver 
    chat_name = request.args.get("chat_name")
    message = request.args.get("message")
    if not chat_name or not message:
        return jsonify({"status": "failure", "error": "Missing chat_name or message"}), 400
    
    get_chat(chat_name)
    message_lines = message.split("\n")

    # Find the message box
    logf(f"✅ Found {chat_name}")
    message_box = driver.find_elements(By.XPATH, "//div[@contenteditable='true']")[-1]
    message_box.click()
    for line in message_lines:
        message_box.send_keys(line)
        message_box.send_keys(Keys.SHIFT, Keys.ENTER)  # New line without sending
    message_box.send_keys(Keys.ENTER)  # Send final message

    message_box.send_keys(Keys.ENTER)

    logf(f"✅ Message sent to {chat_name}")
    clear_search()
    return jsonify({"status": "success", "chat": chat_name, "message": message})

@app.route('/last', methods=['GET'])
def get_last_unread_messages():
    if not authenticated:
        return scan_qr()
    global driver
    
    if driver is None:
        return jsonify({"error": "Selenium driver not initialized"}), 500
    
    # Find the unread messages
    unread_messages = driver.find_elements(By.XPATH, "//span[contains(@aria-label, 'unread message')]")
    n_chats = len(unread_messages)-1
    logf(f"✅ Found {n_chats} Chat's with unread messages")

    chats =[]
    for i, badge in enumerate(unread_messages):
        parent_element = badge.find_element(By.XPATH, "ancestor::div[5]")
        chat_title = parent_element.find_element(By.XPATH, ".//span")
        if (len(chat_title.text) > 1):
            logf(f"🔔 {i}.\t{badge.text} messages from ({chat_title.text})")
            chats.append({"message_count": badge.text, "chat_title": chat_title.text})
    return jsonify({"status": "success", "chats found": n_chats, "chats": chats})

@app.route('/read', methods=['GET'])
def read_chat():
    if not authenticated:
        return scan_qr()
    chat_name = request.args.get("chat_name")
    n_read = int(request.args.get("n_read", 1))
    if not chat_name or not n_read:
        return jsonify({"status": "failure", "error": "Missing chat_name or n_read"}), 400
    
    get_chat(chat_name)

    # Wait for the chat's messages to load completely
    try:
        chat_window = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'selectable-text')]"))
        )
    except Exception as e:
        logf(f"❌ Failed to load chat window: {e}")
        driver.quit()
        return
    
    # Now, grab all messages below the 'Unread Messages' tab
    messages = driver.find_elements(By.XPATH, "//span[contains(@class, 'selectable-text')]")
    logf(f"Found {len(messages)} messages")
    found_messages = []
    if messages:
        # Display the last 'n_read' messages
        for i in range(-n_read, 0):
            last_message = messages[i].text
            logf(f"📨 Message: {last_message}")
            found_messages.append(last_message)
    else:
        logf(f"❌ No messages found in chat with {chat_name}")

    clear_search()

    return jsonify({"status": "success", "chat": chat_name, "messages": found_messages})

@app.route("/version", methods=['GET'])
def show_version():
    if not authenticated:
        return scan_qr()
    return jsonify({"version": version})

@app.route("/")
def index():
    return jsonify({
        "status": "online",
        "endpoints": app.show_all_endpoints()
    })

def start():
    global driver 
    global logfile
    config = configure()
    logfile = open(config.get("Settings", "log_path"), 'w')
    driver = getdriver(config=config, headless=True)  # Start Selenium
    if driver is not None:
        host = "127"
        app.run(port=config.get('Settings', 'port', fallback=5000))
    else:
        logf("Failed to initialize WebDriver")
    logfile.close()

if __name__ == "__main__":
    start()