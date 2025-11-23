# IoT-Enabled Gas Leak & Fire Detection System 🚒💧

**Author:** Aditya  
**Device:** Raspberry Pi Pico W  
**Language:** MicroPython  
**Status:** Completed ✅

## I. Problem Statement
Domestic and industrial fires often originate from undetected gas leakages (LPG/Methane) or electrical short circuits. Traditional alarms are local-only, meaning if no one is home, the hazard goes unnoticed. This project provides a **continuous monitoring system** that detects gas, fire, and heat, sounds a local alarm, activates a fire-suppression pump, and sends instant Telegram alerts to the user.

## II. Scope of Solution
* **Multi-Sensor Monitoring:** Detects Gas (MQ-2), Flame (IR Sensor), and Temperature (DHT22).
* **Active Defense:** Automatically turns on a **Water Pump** when fire is detected.
* **Instant Alerts:** Sends a **Telegram Notification** to the user's phone via Cloud.
* **Data Logging:** Uploads sensor data to **ThingSpeak** every 16 seconds for analytics.

## III. Hardware & Software
**Hardware:**
* Raspberry Pi Pico W
* MQ-2 Gas Sensor
* IR Flame Sensor
* DHT11/DHT22 Temperature Sensor
* 5V Relay Module & Water Pump
* Buzzer & LEDs (Red/Green)

**Software:**
* **IDE:** Thonny IDE
* **Language:** MicroPython
* **Cloud:** ThingSpeak (Data) + Telegram (Alerts)

## IV. Circuit Connections
| Component | Sensor Pin | Pico Pin | Function |
| :--- | :--- | :--- | :--- |
| **MQ-2 Gas** | A0 (Analog) | **GP26** (Pin 31) | Gas Level Detection |
| **IR Flame** | D0 (Digital) | **GP16** (Pin 21) | Flame Detection |
| **DHT22** | Data | **GP27** (Pin 32) | Temperature |
| **Water Pump**| Relay IN | **GP18** (Pin 24) | Active Fire Suppression |
| **Buzzer** | (+) Positive | **GP15** (Pin 20) | Audio Alarm |
| **Red LED** | Anode | **GP14** (Pin 19) | Danger Indicator |
| **Green LED** | Anode | **GP13** (Pin 17) | Safety Indicator |

## V. Key Features
1.  **Smart Logic:** The alarm triggers if Gas > 60% OR Temp > 50°C OR Fire is detected.
2.  **Anti-Spam Alerts:** Telegram messages are triggered via Cloud React logic to prevent phone spamming.
3.  **Robust Connectivity:** Uses Raw Socket communication to prevent memory errors on the Pico W.

## VI. Project Evidence
*(Upload your images to the repo and they will appear here if you name them correctly)*
![Circuit Diagram](circuit_diagram.jpg)
![IoT Dashboard](dashboard.png)
