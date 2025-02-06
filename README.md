# whatsappcli
This tool allows you to automate the process of sending and recieving WhatsApp messages. It's scriptable and headless. It could have many applications including: AI powered Chat Bots, automatic message responses, scheduled messgaes, helpdesk ticketing systems, or even WhatsApp relay for local LoRa mesh radio networks, just to name a few.

## Install

Unix like systems
```
git clone https://github.com/thejostler/whatsappcli
cd whatsappcli
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

Windows (powershell)
```
git clone https://github.com/thejostler/whatsappcli
cd whatsappcli
python -m venv .env
source .\.env\bin\activate
pip install -r requirements.txt
```
## Usage
There are two modes for this tool, client and server.
the whatsapp_web_service.py script starts a headless instance of the Chrome browser and a flask API.

You must run this program either on localhost or on a network attached machine.

The first time you start the service it will try to log you into Whatsapp. A QR code should be displayed in the terminal. Scan this QR from your WhatsApp app to link this headless chrome browser as a device. (The QR code shows as ASCII in order to allow you to log in even over a serial connection or ssh connection)

Once your web_service is running and logged in, you can run whatsapp.py in order to utilize the API.

The first time you run either script, it will automatically generate the `.whatsapp_automation` directory at your User's home directory.

Inside here you can find the logs and configuration files used by this tool. 

### Standalone API
* *IMPORTANT* Remember if you expose this API to the network, anyone who is joined on the network can have unlimited access to your WhatsApp so please use this cautiously

Ordinarily you would want to run your web_service on localhost. However it is possible to expose the API to other clients on the network. This will allow many clients on the network to all use the same instance of Whatsapp Web.

If you want to give network access to your Whatsapp API, do the following:

### On the Web_service machine
1. In the config.cfg file, change the host to 0.0.0.0(to listen on all interfaces), or (the specific ip address you want it to listen on)
2. change the port number if required
3. restart the web_service

### On the client machines
1. In the config.cfg file, change the host to the ip address of your web_service machine
2. Set the port number to the same as the web_service if required

