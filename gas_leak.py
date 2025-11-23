import network
import time
import machine
import dht
import socket
import gc

# --- USER CONFIGURATION ---
SSID = "Test"                    # Your Wi-Fi Name (from log)
PASSWORD = "12345678"  # <--- Update this!
THINGSPEAK_API_KEY = "SN8G3F4JSUV9QLOW" 
THINGSPEAK_HOST = "api.thingspeak.com"

# --- PINS ---
mq2_analog = machine.ADC(26)                     # Gas -> GP26
ir_flame_sensor = machine.Pin(16, machine.Pin.IN)# Flame -> GP16

try:
    dht_sensor = dht.DHT22(machine.Pin(27))      # Temp -> GP27
except:
    dht_sensor = dht.DHT11(machine.Pin(27))

# --- OUTPUTS ---
buzzer = machine.Pin(15, machine.Pin.OUT)        
led_red = machine.Pin(14, machine.Pin.OUT)       
led_green = machine.Pin(13, machine.Pin.OUT)     
water_pump = machine.Pin(18, machine.Pin.OUT)    # Pump -> GP18

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

# --- UPLOAD FUNCTION (Socket) ---
def send_to_thingspeak(gas, fire, alert, temp):
    try:
        gc.collect() 
        addr = socket.getaddrinfo(THINGSPEAK_HOST, 80)[0][-1]
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

# TIMER VARIABLES
last_upload_time = 0
UPLOAD_INTERVAL = 16000 
last_alert_state = 0 

print("System Active. Pump on GP18.")

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
        # Note: Your log showed Gas=53%, so I lowered threshold to 60 for safety, 
        # but if you want it to trigger at 50, change 60.0 to 50.0 below.
        is_gas_leak = gas_pct > 60.0    
        is_fire = is_fire_present == 1
        is_hot = temp_c > 50.0
        
        # 3. ALARM & PUMP TRIGGER
        if is_gas_leak or is_fire or is_hot:
            buzzer.value(0)
            led_red.value(1)
            led_green.value(0)
            water_pump.value(1) 
            
            alert_code = 1
            print(f"🔥 DANGER! Pump Activated! Gas: {gas_pct:.1f}% Fire: {is_fire_present}")
        else:
            buzzer.value(1)
            led_red.value(0)
            led_green.value(1)
            water_pump.value(0)
            
            alert_code = 0
            
        # 4. CLOUD UPLOAD (Smart Logic)
        current_time = time.ticks_ms()
        
        # Upload if 16s passed OR if Danger Status CHANGED (from 0 to 1)
        time_is_up = time.ticks_diff(current_time, last_upload_time) > UPLOAD_INTERVAL
        danger_status_changed = (alert_code != last_alert_state)
        
        if time_is_up or danger_status_changed:
            print(f"Status: Gas={gas_pct:.1f}% Fire={is_fire_present}...", end="")
            send_to_thingspeak(gas_pct, is_fire_present, alert_code, temp_c)
            
            last_upload_time = current_time 
            last_alert_state = alert_code   
            
            time.sleep(1) 

        time.sleep(0.2)

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(1)
