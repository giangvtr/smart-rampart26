# MuseumGuard — Raspberry Pi Pico W water-level node (MicroPython, WiFi -> HTTP).
#
# Flash: install MicroPython on the Pico W, open Thonny, save THIS as main.py.
#
# Wiring (Pico is 3.3V logic):
#   Water sensor VCC -> 3V3 (pin 36)
#   Water sensor GND -> GND
#   Water sensor OUT -> GP26 (ADC0, pin 31)
#
# Assumes your Flask dashboard expects JSON like:
#   {"zone": "GAL01", "raw": 12345, "voltage": 0.62, "level": 19}
# Adjust field names if your /api/ingest expects something else.

import network
import time
import urequests
from machine import ADC, Pin


# ---- config -----------------------------------------------------------------
WIFI_SSID = "Hotspot"
WIFI_PASS = "hahahaha"       # hotspot password
SERVER = "http://192.168.95.204:8000/api/ingest"   # <-- PC's IP on the hotspot + port (dashboard defaults to :8000)
ZONE = "BASE01"        # BASE01 -> BASEMENT (the only zone the dashboard has)

WATER_PIN = 26          # ADC0 on GP26
PERIOD_S = 2            # same 2s heartbeat

# Optional: simple threshold / scaling
RAW_DRY = 3000          # tune with your actual dry reading
RAW_WET = 12000         # tune with your actual wet reading


water_sensor = ADC(Pin(WATER_PIN))
led = Pin("LED", Pin.OUT)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Open network: connect with no key. Passing a password to an open AP
    # makes association fail (endless "connecting..." dots).
    if WIFI_PASS:
        wlan.connect(WIFI_SSID, WIFI_PASS)
    else:
        wlan.connect(WIFI_SSID)
    print("connecting", end="")
    while not wlan.isconnected():
        led.toggle()
        print(".", end="")
        time.sleep(0.3)
    led.on()
    print("\nconnected:", wlan.ifconfig()[0])


def read_water():
    # Average a few samples to reduce noise
    n = 5
    s = 0
    for _ in range(n):
        s += water_sensor.read_u16()
    raw = s // n

    voltage = (raw / 65535) * 3.3

    # Simple linear mapping to 0–100% between dry and wet calibration points
    # Clamp to [0, 100]
    level = (raw - RAW_DRY) * 100 // (RAW_WET - RAW_DRY)
    if level < 0:
        level = 0
    elif level > 100:
        level = 100

    return raw, voltage, level


def main():
    connect_wifi()
    while True:
        try:
            raw, voltage, level = read_water()

            payload = {
                "zone": ZONE,
                "raw": raw,
                "voltage": round(voltage, 3),
                "level": level,
            }

            r = urequests.post(SERVER, json=payload)
            print("sent", payload, "->", r.status_code)
            r.close()
        except OSError as e:
            # A failed read or a dropped POST must never kill the loop.
            print("read/post failed:", e)
        time.sleep(PERIOD_S)


main()