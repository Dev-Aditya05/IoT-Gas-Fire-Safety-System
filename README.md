# IoT-Enabled Gas Leak & Fire Detection System 🚒💧

**Author:** Aditya  
**Device:** Raspberry Pi Pico W  
**Language:** MicroPython  
**Status:** Completed ✅

## I. Problem Statement
Domestic and industrial fires often originate from undetected gas leakages (LPG/Methane) or electrical short circuits. Traditional alarms are local-only, meaning if no one is home, the hazard goes unnoticed. This project provides a **continuous monitoring system** that detects gas, fire, and heat, sounds a local alarm, activates a fire-suppression pump, and sends instant Telegram alerts to the user via the cloud.

## II. Scope of Solution
* **Multi-Sensor Monitoring:** Detects Gas (MQ-2), Flame (IR Sensor), and Temperature (DHT22).
* **Active Defense:** Automatically turns on a **Water Pump** when fire is detected.
* **Instant Alerts:** Sends a **Telegram Notification** to the user's phone via Cloud integration.
* **Data Logging:** Uploads sensor data to **ThingSpeak** every 16 seconds for historical analytics.

## III. Hardware & Software
**Hardware:**
* Raspberry Pi Pico W
* MQ-2 Gas Sensor
* IR Flame Sensor
* DHT11/DHT22 Temperature Sensor
* 5V Relay Module & Water Pump
* Active Buzzer & LEDs (Red/Green)

**Software:**
* **IDE:** Thonny IDE
* **Language:** MicroPython
* **Cloud:** ThingSpeak (Data Visualization) + Telegram (Alerts)

## IV. Circuit Schematic & Connections

The system connects sensors and actuators to the Raspberry Pi Pico W using the following pin configuration. A **5V Relay** is used to isolate the high-power Water Pump from the microcontroller.

### Pin Mapping Table

| Component | Component Pin | Pico Pin | Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| **MQ-2 Sensor** | A0 (Analog) | **GP26** (Pin 31) | Input | Gas concentration (0-100%) |
| **IR Flame Sensor**| D0 (Digital) | **GP16** (Pin 21) | Input | Fire detection (0 = Fire, 1 = Safe) |
| **DHT22** | Data | **GP27** (Pin 32) | Input | Temperature reading |
| **Water Pump** | Relay IN | **GP18** (Pin 24) | Output | Active Fire Suppression |
| **Buzzer** | Positive (+) | **GP15** (Pin 20) | Output | Audio Alarm |
| **Red LED** | Anode (+) | **GP14** (Pin 19) | Output | Danger Indicator |
| **Green LED** | Anode (+) | **GP13** (Pin 17) | Output | Safe Indicator |

> **⚠️ Safety Note:** The Water Pump and MQ-2 heater require an external 5V power source or connection to the VBUS (Pin 40). Do not power the pump directly from a GPIO pin.

![Circuit Diagram](circuit_diagram.jpg)
*(Upload a photo of your wiring or a Wokwi screenshot to your repo and name it circuit_diagram.jpg)*

---

## V. Code Logic Implementation

The system operates on a **non-blocking loop** to ensure instant reaction times while maintaining cloud connectivity.

1.  **Initialization:**
    * Setup GPIO pins for Sensors (Inputs) and Actuators (Outputs).
    * Connect to Wi-Fi (2.4GHz).
    * System Warm-up (2 seconds) to stabilize MQ-2 readings.

2.  **Sensing Loop (Every 0.2s):**
    * **Read:** Analog Gas value, Digital Flame value, and Temperature.
    * **Logic Check:** * IF `Gas > 60%` OR `Fire == Detected` OR `Temp > 50°C`:
            * **Status = DANGER**
            * Turn ON Red LED + Buzzer.
            * Turn ON Water Pump (Relay).
        * ELSE:
            * **Status = SAFE**
            * Turn ON Green LED.
            * Turn OFF Water Pump/Buzzer.

3.  **Cloud Upload Strategy (Smart Logging):**
    * To respect ThingSpeak limits and prevent lag, data is uploaded only when:
        1.  **16 Seconds have passed** since the last upload (Periodic Log).
        2.  **OR** A **New Danger Event** is detected (Instant Alert Trigger).
    * Uses **Raw Socket HTTP** (Direct IP) to prevent memory errors (`MBEDTLS`) common on Pico W.

4.  **Telegram Alerting:**
    * The Pico sends `Field 3 = 1` (Alert Code) to ThingSpeak.
    * ThingSpeak **React App** detects this change and triggers the **Telegram Bot** via API to send a message to the user's phone.

---

## VI. Code for the Solution

Save this file as `main.py` on the Raspberry Pi Pico W.

```python
import network
import time
import machine
import dht
import socket
import gc

# --- USER CONFIGURATION ---
SSID = "Aditya's S21 FE"          
PASSWORD = "YOUR_WIFI_PASSWORD"  
THINGSPEAK_API_KEY = "SN8G3F4JSUV9QLOW" 

# Direct IP used to prevent DNS/SSL Memory Errors
THINGSPEAK_IP = "184.106.153.149" 
THINGSPEAK_HOST = "api.thingspeak.com"

# --- PINS ---
mq2_analog = machine.ADC(26)                     # GP26
ir_flame_sensor = machine.Pin(16, machine.Pin.IN)# GP16

try:
    dht_sensor = dht.DHT22(machine.Pin(27))      # GP27
except:
    dht_sensor = dht.DHT11(machine.Pin(27))

# --- OUTPUTS ---
buzzer = machine.Pin(15, machine.Pin.OUT)        # GP15
led_red = machine.Pin(14, machine.Pin.OUT)       # GP14
led_green = machine.Pin(13, machine.Pin.OUT)     # GP13
water_pump = machine.Pin(18, machine.Pin.OUT)    # GP18 (Relay)

# --- WI-FI CONNECTION ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print(f"Connecting to {SSID}...", end="")
    max_wait = 20
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print(".", end="")
        led_red.toggle()
        time.sleep(1)
        
    if wlan.isconnected():
        print(f"\n✅ Connected! IP: {wlan.ifconfig()[0]}")
        led_red.value(0); led_green.value(1)
        buzzer.value(1); time.sleep(0.1); buzzer.value(0)
    else:
        print("\n❌ Wi-Fi Failed.")
        while True: led_red.toggle(); time.sleep(0.1) 

# --- UPLOAD FUNCTION ---
def send_to_thingspeak(gas, fire, alert, temp):
    try:
        gc.collect() 
        # Connect to Direct IP
        addr = (THINGSPEAK_IP, 80)
        s = socket.socket()
        s.settimeout(6.0) 
        s.connect(addr)
        
        path = f"/update?api_key={THINGSPEAK_API_KEY}&field1={gas:.1f}&field2={fire}&field3={alert}&field4={temp:.1f}"
        request = f"GET {path} HTTP/1.1\r\nHost: {THINGSPEAK_HOST}\r\nConnection: close\r\n\r\n"
        
        s.send(request.encode())
        s.recv(128) 
        s.close()
        print(" ☁️ Cloud Updated.")
    except Exception as e:
        print(f" ⚠️ Upload Skipped: {e}")

# --- MAIN LOOP ---
print("System Warming Up...")
time.sleep(2)
connect_wifi()

last_upload_time = 0
UPLOAD_INTERVAL = 16000 
last_alert_state = 0 

print("System Active.")

while True:
    try:
        # 1. READ SENSORS
        gas_raw = mq2_analog.read_u16()
        gas_pct = (gas_raw / 65535) * 100
        
        fire_val = ir_flame_sensor.value()
        is_fire_present = 1 if fire_val == 0 else 0
        
        try:
            dht_sensor.measure()
            temp_c = dht_sensor.temperature()
        except:
            temp_c = 0.0 

        # 2. SAFETY LOGIC
        is_gas_leak = gas_pct > 60.0    
        is_fire = is_fire_present == 1
        is_hot = temp_c > 50.0
        
        # 3. ALARM & PUMP TRIGGER
        if is_gas_leak or is_fire or is_hot:
            buzzer.value(1)
            led_red.value(1)
            led_green.value(0)
            water_pump.value(1) # PUMP ON
            
            alert_code = 1
            print(f"🔥 DANGER! Pump Activated! Gas: {gas_pct:.1f}% Fire: {is_fire_present}")
        else:
            buzzer.value(0)
            led_red.value(0)
            led_green.value(1)
            water_pump.value(0) # PUMP OFF
            
            alert_code = 0
            
        # 4. CLOUD UPLOAD
        current_time = time.ticks_ms()
        
        # Upload if 16s passed OR if Status Changed (Safe <-> Danger)
        time_is_up = time.ticks_diff(current_time, last_upload_time) > UPLOAD_INTERVAL
        status_changed = (alert_code != last_alert_state)
        
        if time_is_up or status_changed:
            print(f"Status: Gas={gas_pct:.1f}% Fire={is_fire_present}...", end="")
            send_to_thingspeak(gas_pct, is_fire_present, alert_code, temp_c)
            
            last_upload_time = current_time 
            last_alert_state = alert_code   
            time.sleep(1) 

        time.sleep(0.2)

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(1)
```

---

## VII. IoT Dashboard Analytics & Data

The system utilizes **ThingSpeak** for real-time data visualization and historical logging. The dashboard provides a comprehensive view of the environmental conditions and system status.

**Channel ID:** `3172254`  
**Update Interval:** Every 16 seconds (or instantly upon Danger detection)

### Dashboard Fields Description

The data is mapped to the following ThingSpeak fields:

* **Field 1: Gas Concentration (%)**
    * *Sensor:* MQ-2 Gas Sensor
    * *Description:* Displays the real-time percentage of combustible gas in the air.
    * *Threshold:* Values above **60%** indicate a leak.

* **Field 2: Fire Detection Status**
    * *Sensor:* IR Flame Sensor
    * *Description:* Binary visualization of fire presence.
    * *Values:* `0` = Safe, `1` = Fire Detected.

* **Field 3: System Alert Trigger**
    * *Logic:* Combined logic of Gas, Fire, and Temperature.
    * *Description:* This field acts as the trigger for the **Telegram Bot**.
    * *Values:* `1` = Danger (Triggers Message), `0` = Safe.

* **Field 4: Temperature (°C)**
    * *Sensor:* DHT22 (or DHT11)
    * *Description:* Monitors ambient room temperature to detect heat spikes caused by fire.
    * *Threshold:* Values above **50°C** contribute to the alarm trigger.

### Live Dashboard Preview

Below is a snapshot of the analytics dashboard showing a simulated fire event:

![IoT Dashboard](dashboard.png)
*(Note: Please upload a screenshot of your actual ThingSpeak graphs to the repository and name it `dashboard.png` for this image to appear)*
