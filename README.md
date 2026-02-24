### create virtual env
python3 -m venv venv

### activate virtual environment
source venv/bin/activate

### install requirements
pip3 install -r requirements.txt

### install mosquitto via homebrew
brew install mosquitto

### start mosquitto broker
brew services start mosquitto

### update the config file for setting up local mosquitto broker (/usr/local/etc/mosquitto/mosquitto.conf)
```
# mosquitto.conf

# Listen on local port 1883
listener 1883

# Allow connections without username/password
allow_anonymous true

# Log to stdout for debugging
log_type all
```
## Steps to run the program

### Start mosquitto broker
mosquitto -v

### Start publisher
python3 publisher.py

### Start device
python3 device.py

### Start subscriber
python3 subscriber.py