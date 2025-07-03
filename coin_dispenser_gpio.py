"""
pip3 uninstall RPi.GPIO

sudo apt update
sudo apt install python3-lgpio # ติดตั้ง lgpio library
pip3 install gpiozero
"""

import time
import threading
import queue
from gpiozero import DigitalInputDevice, DigitalOutputDevice, Button
# from signal import pause # ไม่ได้ใช้ใน module นี้โดยตรง แต่ใช้ในตัวอย่างการรันเอง

# --- GPIO Configuration ---
BILER_SENSOR_PIN = 6  # ขาสำหรับตรวจจับเซนเซอร์ ธนบัตร (นับการกะพริบ/พัลส์)
COIN_SENSOR_PIN = 12  # ขาสำหรับตรวจจับการหมุนของเซ็นเซอร์เหรียญ
GPIO_RELAY = 26       # ขาสำหรับควบคุม Relay (เช่น เครื่องจ่ายเหรียญ)

# --- Global State Variables for Dispenser ---
coins_to_dispense_target = 0
coins_dispensed_count = 0
is_dispensing_active = False

# --- Global State Variables for Biller Pulse Counting ---
bill_pulse_count = 0
last_bill_pulse_time = 0
BILL_PULSE_TIMEOUT = 1.0 # วินาที: ระยะเวลาสูงสุดที่ไม่มีการกะพริบก่อนที่จะถือว่าการนับจบ
# Mapping จำนวนพัลส์กับมูลค่าธนบัตร (คุณอาจต้องปรับค่าเหล่านี้ตามการทดสอบจริง)
BILL_PULSE_MAPPING = {
    2: 20,   # 2 พัลส์ = 20 บาท
    5: 50,   # 5 พัลส์ = 50 บาท
    10: 100, # 10 พัลส์ = 100 บาท
    50: 500, # 50 พัลส์ = 500 บาท
    100: 1000 # 100 พัลส์ = 1000 บาท (ถ้าเซ็นเซอร์รองรับ)
}

# --- Threading Event for Biller Value Notification ---
# Event นี้จะถูก set เมื่อตรวจจับและยืนยันมูลค่าธนบัตรได้
# เพื่อให้ main application (Kivy GUI) สามารถรับรู้ได้ว่ามีการหยอดเงินและจำนวนเท่าไหร่
biller_value_detected_event = threading.Event()
detected_bill_value_amount = 0 # เก็บมูลค่าธนบัตรที่ตรวจจับได้

# --- GPIO Zero Objects ---
# Relay (Active Low): initial_value=False ทำให้ Relay เริ่มต้นในสถานะ OFF (ขา GPIO HIGH)
relay = DigitalOutputDevice(GPIO_RELAY, active_high=False, initial_value=False)

# Sensors (Button object มี debounce ในตัว)
# pull_up=True คือการใช้ Resistor ภายในของ Raspberry Pi ดึงสัญญาณขึ้น (เหมาะกับปุ่ม/เซ็นเซอร์ที่ต่อลงกราวด์เมื่อทำงาน)
# bounce_time ในหน่วยวินาที (0.02s = 20ms, 0.05s = 50ms)
biller_sensor = Button(BILER_SENSOR_PIN, pull_up=True, bounce_time=0.01)
coin_sensor = Button(COIN_SENSOR_PIN, pull_up=True, bounce_time=0.01)


# --- Relay Control Function ---
def set_relay_state(state):
    """
    ตั้งค่าสถานะของ Relay (เปิด/ปิด)
    state: True สำหรับ ON, False สำหรับ OFF (สำหรับ DigitalOutputDevice)
    """
    if state: # True = ON (ซึ่งจะส่ง LOW ออกไปที่ขา GPIO เพราะ active_high=False)
        relay.on()
        print("[Relay] state set to: ON")
    else: # False = OFF (ซึ่งจะส่ง HIGH ออกไปที่ขา GPIO เพราะ active_high=False)
        relay.off()
        print("[Relay] state set to: OFF")

# --- Biller Sensor Callback (GPIO Zero) ---
def biler_sensor_callback_gpiozero():
    """
    Callback สำหรับเซ็นเซอร์ธนบัตร (ใช้ GPIO Zero Button object)
    เมื่อเซ็นเซอร์ตรวจจับการเปลี่ยนแปลงสถานะ (กดปุ่ม / กะพริบ) จะนับพัลส์
    Note: 'when_pressed' จะตรวจจับเมื่อสถานะเปลี่ยนเป็น active state (LOW ถ้า pull_up=True)
    """
    global bill_pulse_count, last_bill_pulse_time
    bill_pulse_count += 1
    last_bill_pulse_time = time.time()
    print("bill_pulse_count",bill_pulse_count)

    print(f"[Biller] Pulse Detected! Current count: {bill_pulse_count}")

# --- Coin Sensor Callback (GPIO Zero) ---
def coin_sensor_callback_gpiozero():
    """
    Callback สำหรับเซ็นเซอร์เหรียญ (ใช้ GPIO Zero Button object)
    นับจำนวนเหรียญที่ถูกจ่ายออกไป และหยุด Relay เมื่อจ่ายครบตามเป้าหมาย
    Note: 'when_pressed' จะตรวจจับเมื่อสถานะเปลี่ยนเป็น active state (LOW ถ้า pull_up=True)
    คุณอาจต้องใช้ 'when_released' หรือ 'when_activated' ขึ้นอยู่กับเซ็นเซอร์
    """
    global coins_dispensed_count, is_dispensing_active
    #print("coin_sensor_callback_gpiozero",coins_dispensed_count)
    #if is_dispensing_active:
    coins_dispensed_count += 1
    print(f"[Coin] Detected: {coins_dispensed_count} / {coins_to_dispense_target}")
        
    if coins_dispensed_count >= coins_to_dispense_target:
        print("[Coin] Dispensing complete. Stopping Relay.")
        is_dispensing_active = False
        set_relay_state(False) # ปิด Relay

# --- Dispensing Logic ---
def start_dispensing(num_coins):
    """
    เริ่มต้นกระบวนการจ่ายเหรียญตามจำนวนที่กำหนด
    ฟังก์ชันนี้จะถูกเรียกจากแอป Kivy เมื่อมีการชำระเงินสำเร็จ (QR Code)
    หรือเรียกจาก Biller Processing Thread เมื่อตรวจพบธนบัตร
    """
    global coins_to_dispense_target, coins_dispensed_count, is_dispensing_active

    if is_dispensing_active:
        print("[Dispenser] Already dispensing. Please wait.")
        return False # แจ้งว่าไม่สามารถเริ่มได้

    if num_coins <= 0:
        print("[Dispenser] Number of coins to dispense must be greater than 0.")
        return False

    print(f"[Dispenser] Starting to dispense {num_coins} coins...")
    coins_to_dispense_target = num_coins
    coins_dispensed_count = 0
    is_dispensing_active = True
    set_relay_state(True) # เปิด Relay
    return True # แจ้งว่าเริ่มได้

# --- Biller Processing Thread ---
def process_biller_pulses_thread():
    """
    เธรดสำหรับตรวจสอบจำนวนพัลส์ธนบัตรที่นับได้จาก Biller Callback
    และสั่งจ่ายเหรียญตามมูลค่าที่ยืนยันแล้ว
    """
    global bill_pulse_count, last_bill_pulse_time, detected_bill_value_amount

    print("[Biller Processor] Thread started.")
    while True:
        current_time = time.time()
        
        # ตรวจสอบว่ามีพัลส์ถูกนับเข้ามา และผ่านช่วง Timeout ไปแล้ว
        # นั่นหมายความว่าการนับสำหรับธนบัตรใบนี้ได้สิ้นสุดลง
        if bill_pulse_count > 0 and (current_time - last_bill_pulse_time) > BILL_PULSE_TIMEOUT:
            print(f"[Biller Processor] Pulse counting finished. Total pulses: {bill_pulse_count}")
            
            # ตรวจสอบมูลค่าธนบัตรจากจำนวนพัลส์ที่นับได้
            detected_bill_value = BILL_PULSE_MAPPING.get(bill_pulse_count)
            
            if detected_bill_value:
                if not is_dispensing_active:
                    print(f"[Biller Processor] Detected {detected_bill_value} Baht (from {bill_pulse_count} pulses).")
                    # แจ้งมูลค่าที่ตรวจจับได้ไปยังภายนอก (ผ่าน Global variable และ Event)
                    detected_bill_value_amount = detected_bill_value
                    biller_value_detected_event.set() # Set event เพื่อแจ้ง Kivy App (ถ้าต้องการ)
                    
                    # แปลงมูลค่าธนบัตรเป็นจำนวนเหรียญที่ต้องการจ่าย (สมมติ 1 เหรียญ = 10 บาท)
                    num_coins_to_dispense = detected_bill_value // 10 
                    start_dispensing(num_coins_to_dispense)
                else:
                    print(f"[Biller Processor] Received {detected_bill_value} Baht but dispensing is active. Ignoring for now.")
            else:
                print(f"[Biller Processor] Unknown pulse count: {bill_pulse_count}. Possibly an error or invalid bill.")
            
            # รีเซ็ตตัวนับพัลส์หลังจากประมวลผลแล้ว
            bill_pulse_count = 0
            last_bill_pulse_time = 0
            biller_value_detected_event.clear() # Clear event หลังจากประมวลผลแล้ว

        time.sleep(0.01) # หน่วงเวลาเล็กน้อยเพื่อให้เธรดอื่นๆ ทำงาน


# --- Module Initialization (runs when this file is imported) ---
# ผูก Callback functions เข้ากับ GPIO Zero Objects
biller_sensor.when_pressed = biler_sensor_callback_gpiozero
coin_sensor.when_pressed = coin_sensor_callback_gpiozero 

# เริ่มเธรดประมวลผล Biller โดยอัตโนมัติเมื่อ module ถูก import
biller_process_thread = threading.Thread(target=process_biller_pulses_thread)
biller_process_thread.daemon = True # ทำให้เธรดปิดเมื่อโปรแกรมหลักปิด
biller_process_thread.start()

# ตั้งค่า Relay ให้เป็น OFF ทันทีที่ module โหลด (แก้ไขปัญหา Relay ทำงานเอง)
set_relay_state(False) 

print("coin_dispenser_gpio module loaded with GPIO Zero. Relay initialized to OFF.")


# --- Main execution block for direct testing ---
# ส่วนนี้จะถูกเรียกใช้เมื่อไฟล์นี้ถูกรันโดยตรง (python3 coin_dispenser_gpio.py)
if __name__ == '__main__':
    from signal import pause # นำเข้า pause สำหรับการรันโดยตรง

    print("Running coin_dispenser_gpio.py directly for testing...")
    
    print("\nSystem ready. Press Ctrl+C to exit.")
    print("Simulate Biller pulses by manually triggering GPIO 6.")
    print("Call start_dispensing(X) from Python shell to simulate payment initiated dispense.")

    try:
        # Loop หลักเพื่อรันโปรแกรมไปเรื่อยๆ รอ Events จาก GPIO Zero
        pause() # Keep the script running, waiting for events

    except KeyboardInterrupt:
        print("\nExiting program.")
    finally:
        # GPIO Zero จัดการ cleanup โดยอัตโนมัติเมื่อโปรแกรมจบ
        # แต่เพื่อความมั่นใจ ให้ Relay ปิด
        set_relay_state(False) 
        print("Program terminated.")

