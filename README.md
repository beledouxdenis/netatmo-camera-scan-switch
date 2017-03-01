# netatmo-camera-scan-switch
Enable / Disable the Netatmo cameras according to devices in the local network

The point is to disable the camera when you are at home, so it doesn't record what you are doing.
I guess I am not the only one concerned by this.

# Installation
Download `netatmo.py` in the folder of your choice and make it executable
```
mkdir ~/netatmo
cd ~/netatmo
wget https://raw.githubusercontent.com/beledouxdenis/netatmo-camera-scan-switch/master/netatmo.py
chmod +x netatmo.py
```
This script uses OAuth tokens to authenticate

You have to create a new app on the Netatmo website, and save the `client_id` and `client_secret` in the given variables in `netatmo.py`

https://dev.netatmo.com/dev/resources/technical/samplessdks/tutorials
```
vim netatmo.py
```
Then, assign the variables `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET`.

Then, execute the script manually:
```
./netatmo.py
```
It will ask you your Netatmo credentials. They will be used only to get the OAuth tokens. They won't be stored, only the access tokens will be.

It will then display your home(s) data. Look for the ids of the cameras you want to enable/disable according to your devices presence in your local network, and set them in the list `CAMERA_IDS`. Optionally, you can specify the id of the home in the variable `HOME_ID`.

In the `DEVICES` dictionary, set your devices IP. If the IP is present in your network, the camera(s) will be disabled. If the IP doesn't respond after 5 minutes (can be customized with the variable `TIME_BEFORE_ENABLE`), the camera will be re-enabled.

Obviously, setting static IP addresses for your devices is advised.

You can combine IP adresses with `AND` or `OR` operators:
```
DEVICES = {
    'Sarah': {
        'ip': '192.168.1.10',
    },
    'John': {
        'ip': '192.168.1.11',
        'ip': '192.168.1.12',
    }
}
```
With the above example:
 - `Sarah` will be considered present as soon as the IP `192.168.1.10` is present on the local network.
 - `John` will be considered present if both `192.168.1.11` and `192.168.1.12` are present on the local network.

 Once all this configured, you can make this script called from a cron every minute:
 ```
 crontab -e
 */1 * * * * /home/pi/netatmo/netatmo.py
 ```

# Remarks
## Security
One can say that using IP adresses is not very safe, that a thief could configure his phone network to use the same static IP address than what you configured to be able to disable your camera.
I will reply this:
 - First, the thief has to be aware that you use such a security.
 - Then, he must have access to the local network. That means either he has a device with ethernet, and he can find an ethernet port in your home, or he knows your WiFi password key.
 - Then, he must know the static IP that you configured.

I don't know for you, but in my opinion this is already a lot of things the thief must know before being able to disable your camera with this system.

## API
This script uses the official Netatmo API.
However, it uses an undocumented command, on the camera: `changestatus`.
This is the command which is used when you enable/disable your camera from the Netatmo app or web interface.
This is therefore not that unlikely that a change by Netatmo side breaks this script.
For instance, recently, I was no longer able to perform this command using the `vpn_url` of the camera, I had to use the local URL of the camera.

# Go Further
This script is meant to be improved. Pull requests are welcome.
For instance, you can create a new presence scan method (e.g. Bluetooth, or Wireless SSID).
You just have to create a new method in the `util` class, such as:
```
@staticmethod
def scan_bluetooth(addresses):
    return [address for address in addresses if os.system("something with this address") == 0]
```
that take as parameter a list of things (string, float, whatever) and returns the ones that are present.
Then, you can add in the `DEVICES` dictionary the addresses of your devices for this new scan method, such as:
```
DEVICES = {
    'sarah': {
        'bluetooth': 'aa:bb:cc:dd:ee',
    },
}
```
