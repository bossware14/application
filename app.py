"""
sudo apt update
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install pkg-config
pip install kivy
pip install requests

ฉันจะการให้แอปมี Gui เพื่อให้ลูกค้า สะดวก สามารถโอนเงินผ่าน QRCode ได้ โดยฉันมี Api ด้วย

ฉันมี Pi5 ต่อจอ LCD Touch 7Inch แล้ว
API Payment :
ApiKey = F8C04-06726831FD

การสร้างการชำระเงิน
https://payment.all123th.com/api-pay?amount=10&secretKey=F8C04-06726831FD&username=coin_matchine_01

ผลลับ json
data = {
  "refId": "8EBC55C56CFB7C315D0EDCC5E10975CF",
  "date": "2025-07-04",
  "time": "00:48:57",
  "Agent": "admin",
  "number": "010753700088205",
  "amount": "5.00",
  "type": "tung",
  "ref": "TI0675560P7001856ZO",
  "ref1": "F74A35BDFE8529B12CBR",
  "ref2": "0000219968f0a068879d",
  "detail": "BR",
  "remark": "",
  "secret": "258d73cadb425a8feef8897184b07f84ad7e7dcd",
  "username": "Test02",
  "qrcode": "00020101021130860016A00000067701011201150107537000882050219TI0675560P7001856ZO0320F74A35BDFE8529B12CBR530376454045.005802TH622407200000219968f0a068879d63044D53",
  "status": "pedding",
  "endtime": "2025-07-04 00:53:57",
  "ref_no": "2009406",
  "img": "https://image-charts.com/chart?chs=150x150&cht=qr&choe=UTF-8&chl=00020101021130860016A00000067701011201150107537000882050219TI0675560P7001856ZO0320F74A35BDFE8529B12CBR530376454045.005802TH622407200000219968f0a068879d63044D53",
  "url": "https://payment.all123th.com/payment?ref_no=8EBC55C56CFB7C315D0EDCC5E10975CF",
  "url_check": "https://api.all123th.com/payment-swiftpay/8EBC55C56CFB7C315D0EDCC5E10975CF?type=json"
}

โดยเราจะแสดงหน้าผ่าน data.url  ก็ได้
หรือถ้าไม่ได้ ก็แสดง data.img (รูปภาพ QRCode) และคอยเชค url_check เพื่อตรวจสอบการชำระเงินก็ได้ เมื่อชำระเงินเสร็จเครื่องก้จะจ่ายเงินเหรียญตามที่ตั้งไว้ สามารถใช้ได้ 2 ระบบคือ สแกนจ่าย(payment) และ หยอดธนบัตร ปกติ

ต้องการให้แอป เต็มจอ fullscreen
- หน้าแสดง ข้อความและ รูปภาพ(โฆษณา)
- หน้าเลือกจำนวนเงิน 20,30,50,100
- หน้าชำระเงิน หมดเวลา 30 วินาที
- หน้า thankyou
- หน้าตั้งค่า - 



ps aux | grep python


######### Auto Start #####
mkdir -p /home/pi5/.config/autostart/
nano /home/pi5/.config/autostart/kiosk_app.desktop
############
[Desktop Entry]
Type=Application
Name=Coin Machine App
Exec=/usr/bin/python3 /home/pi5/Desktop/application/app.py
# หรือถ้าคุณต้องการรันด้วย sudo (ซึ่งไม่แนะนำสำหรับ GUI แต่ถ้าจำเป็นจริงๆ)
# Exec=sudo /usr/bin/python3 /home/pi5/Desktop/application/app.py
# แต่ต้องระวังปัญหา X server authentication ตามที่เราเคยคุยกัน

# WorkingDirectory คือ Path ที่ไฟล์ app.py อยู่ ซึ่งจำเป็นเพื่อให้ Python หา module อื่นๆ ได้
WorkingDirectory=/home/pi5/Desktop/application/
Comment=Kivy application for coin dispensing machine
Terminal=false
# NoDisplay=true # ถ้าคุณไม่ต้องการให้ไอคอนนี้แสดงในเมนู

##############
"""
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp

# --- สำหรับการรองรับภาษาไทย ---
import os
from kivy.core.text import LabelBase

# กำหนด Font สำหรับภาษาไทย
# ตรวจสอบให้แน่ใจว่า 'fonts/NotoSansThai-Regular.ttf' คือ path ที่ถูกต้อง
# คุณต้องคัดลอกไฟล์ฟอนต์ NotoSansThai-Regular.ttf (หรือฟอนต์ไทยอื่นๆ)
# ไปไว้ในโฟลเดอร์ 'fonts' ที่อยู่ในไดเรกทอรีเดียวกับ app.py
FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'NotoSansThai-Regular.ttf')
LabelBase.register(name='Roboto', fn_regular=FONT_PATH) # ทับ font default ของ Kivy

import requests
import json
import threading
import time


# --- Import GPIO Control Module ---
# ตรวจสอบให้แน่ใจว่าไฟล์ coin_dispenser_gpio.py อยู่ในไดเรกทอรีเดียวกัน
# และเป็นเวอร์ชันที่ใช้ GPIO Zero แล้ว
import coin_dispenser_gpio as c_gpio 

# --- Global Configuration ---
# ชื่อไฟล์ config ที่จะใช้เก็บและโหลดค่าต่างๆ
CONFIG_FILE = 'config.json' 

# ค่าเริ่มต้น (Default Values) สำหรับการตั้งค่า
# จะถูกใช้หากไฟล์ config.json ไม่พบหรือไม่สามารถโหลดได้
APP_CONFIG = {
    "api_key": "F8C04-06726831FD",
    "username": "coin_matchine_01",
    "admin_password": "123456",
    "coin_per_baht_ratio": 10, # จำนวนเหรียญที่จ่ายต่อ 1 บาท (เช่น ถ้า 1 เหรียญ = 10 บาท, ใส่ 0.1 หรือถ้า 1 เหรียญ = 1 บาท, ใส่ 1)
    "payment_timeout_seconds": 30
}

# Base URLs สำหรับ Payment API
BASE_PAYMENT_URL = "https://payment.all123th.com/api-pay"
CHECK_STATUS_BASE_URL = "https://api.all123th.com/payment-swiftpay/"

# --- Fullscreen Setup ---
Window.fullscreen = 'auto' # ทำให้แอปแสดงผลเต็มจอ

# --- Config Management Functions ---
def load_config():
    """
    โหลดค่าการตั้งค่าจากไฟล์ JSON.
    หากไฟล์ไม่มีหรือมีข้อผิดพลาดในการอ่าน จะใช้ค่าเริ่มต้น.
    """
    global APP_CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                # อัปเดต APP_CONFIG ด้วยค่าที่โหลดมา หากมี
                APP_CONFIG.update(loaded_config)
            print(f"[Config] Config loaded from {CONFIG_FILE}")
        except json.JSONDecodeError:
            print(f"[Config] Error decoding JSON from {CONFIG_FILE}. Using default config.")
        except Exception as e:
            print(f"[Config] An error occurred while loading config: {e}. Using default config.")
    else:
        print(f"[Config] Config file {CONFIG_FILE} not found. Using default config.")
    
    # เพื่อให้มั่นใจว่ามีไฟล์ config ที่ถูกต้องอยู่เสมอ
    save_config() 

def save_config():
    """
    บันทึกค่าการตั้งค่าปัจจุบันลงในไฟล์ JSON.
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(APP_CONFIG, f, indent=4) # indent=4 เพื่อให้อ่านง่าย
        print(f"[Config] Config saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"[Config] An error occurred while saving config: {e}")

# --- Screen Definitions ---

class WelcomeScreen(Screen):
    """
    หน้าจอเริ่มต้น/โฆษณา
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'welcome'
        
        layout = BoxLayout(orientation='vertical')
        
        # ส่วนแสดงรูปภาพโฆษณา (ใช้ AsyncImage สำหรับโหลดจาก URL หรือ Image สำหรับไฟล์โลคอล)
        # แนะนำให้ใช้รูปภาพในเครื่องเพื่อหลีกเลี่ยงปัญหาอินเทอร์เน็ตช่วงเริ่มต้นแอป
        # อย่าลืมสร้างโฟลเดอร์ 'images' และใส่รูปภาพ 'ad_placeholder.png' ไว้
        self.ad_image = AsyncImage(source='images/ad_placeholder.png', 
                                    size_hint=(1, 0.7))
        layout.add_widget(self.ad_image)

        # ปุ่มเริ่มใช้งาน
        start_button = Button(text='แตะเพื่อเริ่ม', 
                              font_size=dp(40), 
                              size_hint=(1, 0.2), # ลดขนาดปุ่มเพื่อให้มีที่ว่าง
                              background_color=(0.2, 0.7, 0.2, 1))
        start_button.bind(on_release=self.go_to_amount_selection)
        layout.add_widget(start_button)

        # ปุ่มสำหรับ Admin/ตั้งค่า (อาจจะเล็กหรืออยู่มุมจอ)
        admin_button = Button(text='Admin', 
                              font_size=dp(20), 
                              size_hint=(1, 0.1), 
                              background_color=(0.5, 0.5, 0.5, 1))
        admin_button.bind(on_release=self.show_admin_popup)
        layout.add_widget(admin_button)

        self.add_widget(layout)
        
    def go_to_amount_selection(self, instance):
        self.manager.current = 'amount_selection'

    def show_admin_popup(self, instance):
        # เรียกฟังก์ชันแสดง Popup รหัสผ่านจาก SettingsScreen
        self.manager.get_screen('settings').show_password_popup(self.manager)


class AmountSelectionScreen(Screen):
    """
    หน้าจอเลือกจำนวนเงิน
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'amount_selection'

        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        layout.add_widget(Label(text='กรุณาเลือกจำนวนเงิน', font_size=dp(50), size_hint_y=0.2))

        # ปุ่มเลือกจำนวนเงิน
        button_grid = GridLayout(cols=2, spacing=dp(20), size_hint_y=0.7)
        amounts = [20, 30, 50, 100] # จำนวนเงินที่สามารถเลือกได้
        for amount in amounts:
            btn = Button(text=f'{amount} บาท', font_size=dp(50), background_color=(0.2, 0.5, 0.8, 1))
            btn.bind(on_release=lambda x, a=amount: self.select_amount(a))
            button_grid.add_widget(btn)
        
        layout.add_widget(button_grid)

        # ปุ่มย้อนกลับ
        back_button = Button(text='ย้อนกลับ', 
                             font_size=dp(30), 
                             size_hint_y=0.1,
                             background_color=(0.8, 0.4, 0.2, 1))
        back_button.bind(on_release=self.go_back_to_welcome)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def select_amount(self, amount):
        print(f"[Amount Selection] Selected amount: {amount} Baht")
        self.manager.get_screen('payment').set_payment_amount(amount)
        self.manager.current = 'payment'

    def go_back_to_welcome(self, instance):
        self.manager.current = 'welcome'

class PaymentScreen(Screen):
    """
    หน้าจอชำระเงิน แสดง QR Code และนับถอยหลัง
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'payment'
        
        self.payment_amount = 0
        self.ref_id = None
        self.check_url = None
        self.payment_timer = None
        self.check_status_event = None

        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        self.amount_label = Label(text='จำนวนเงิน: 0 บาท', font_size=dp(40), size_hint_y=0.15)
        layout.add_widget(self.amount_label)

        self.qr_image = AsyncImage(source='', size_hint=(1, 0.6))
        layout.add_widget(self.qr_image)

        # ใช้ค่า payment_timeout_seconds จาก APP_CONFIG
        self.timer_label = Label(text=f'เวลาเหลือ: {APP_CONFIG["payment_timeout_seconds"]} วินาที', font_size=dp(35), size_hint_y=0.1)
        layout.add_widget(self.timer_label)

        # ปุ่มยกเลิก
        cancel_button = Button(text='ยกเลิก', 
                               font_size=dp(30), 
                               size_hint_y=0.15,
                               background_color=(0.8, 0.2, 0.2, 1))
        cancel_button.bind(on_release=self.cancel_payment)
        layout.add_widget(cancel_button)

        self.add_widget(layout)
    
    def set_payment_amount(self, amount):
        self.payment_amount = amount
        self.amount_label.text = f'จำนวนเงิน: {amount} บาท'
        self.timer_label.text = f'เวลาเหลือ: {APP_CONFIG["payment_timeout_seconds"]} วินาที' # รีเซ็ตข้อความเวลา

    def on_enter(self):
        """
        เมื่อเข้าสู่หน้านี้ จะเริ่มกระบวนการสร้าง QR Code และ Timer
        """
        self.qr_image.source = 'https://via.placeholder.com/200x200.png?text=Generating+QR...' # Placeholder QR
        self.qr_image.reload() # Force reload placeholder
        self.start_payment_process()

    def on_leave(self):
        """
        เมื่อออกจากหน้านี้ ให้หยุด Timer และการตรวจสอบสถานะ
        """
        if self.payment_timer:
            self.payment_timer.cancel()
        if self.check_status_event:
            self.check_status_event.cancel()
        self.ref_id = None
        self.check_url = None
        print("[Payment] Payment process stopped.")

    def start_payment_process(self):
        """
        เริ่มต้นการสร้าง QR Code และ Timer
        """
        print(f"[Payment] Requesting QR code for amount: {self.payment_amount}")
        self.payment_start_time = time.time()
        
        # เริ่ม Timer นับถอยหลัง
        if self.payment_timer:
            self.payment_timer.cancel() 
        self.payment_timer = Clock.schedule_interval(self.update_timer, 1)

        # เริ่มเธรดสร้าง QR Code เพื่อไม่ให้ GUI ค้าง
        threading.Thread(target=self._request_qr_code).start()

    def _request_qr_code(self):
        """
        เรียก Payment API เพื่อสร้าง QR Code (ทำงานในเธรดแยก)
        """
        try:
            # ใช้ค่า API_KEY และ USERNAME จาก APP_CONFIG
            url = f"{BASE_PAYMENT_URL}?amount={self.payment_amount}&secretKey={APP_CONFIG['api_key']}&username={APP_CONFIG['username']}"
            print(f"[Payment] Calling API: {url}")
            response = requests.get(url, timeout=10) # เพิ่ม timeout ป้องกันการค้าง
            response.raise_for_status() # ตรวจสอบ HTTP errors (เช่น 404, 500)

            data = response.json()
            print(f"[Payment] API Response: {json.dumps(data, indent=2)}")

            if data and data.get('status') == 'pedding':
                qr_img_url = data.get('img') # URL ของรูปภาพ QR Code
                self.ref_id = data.get('refId') # ID อ้างอิงสำหรับการตรวจสอบสถานะ
                self.check_url = f"{CHECK_STATUS_BASE_URL}{self.ref_id}?type=json" # URL สำหรับตรวจสอบสถานะ

                if qr_img_url:
                    Clock.schedule_once(lambda dt: self.update_qr_image(qr_img_url))
                    # เริ่มตรวจสอบสถานะการชำระเงินใน Background
                    if self.check_status_event:
                        self.check_status_event.cancel()
                    self.check_status_event = Clock.schedule_interval(self._check_payment_status, 3) # ตรวจสอบทุก 3 วินาที
                else:
                    print("[Payment] Error: No QR image URL in response.")
                    Clock.schedule_once(lambda dt: self.show_error_popup("QR Code Error", "ไม่สามารถสร้าง QR Code ได้ (URL รูปภาพไม่พบ)"))
            else:
                print(f"[Payment] API response status not pedding: {data.get('status')}")
                Clock.schedule_once(lambda dt: self.show_error_popup("API Error", "การสร้าง QR Code ล้มเหลว (สถานะไม่ถูกต้อง)"))

        except requests.exceptions.Timeout:
            print(f"[Payment] API request timed out.")
            Clock.schedule_once(lambda dt: self.show_error_popup("Network Error", "API ตอบสนองช้าเกินไป ลองใหม่อีกครั้ง"))
        except requests.exceptions.RequestException as e:
            print(f"[Payment] Network or API error: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Network Error", f"ไม่สามารถเชื่อมต่อ Payment API ได้: {e}"))
        except json.JSONDecodeError as e:
            print(f"[Payment] JSON Decode Error: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Data Error", "รูปแบบข้อมูลจาก Payment API ไม่ถูกต้อง"))
        except Exception as e:
            print(f"[Payment] An unexpected error occurred: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Error", f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}"))

    def update_qr_image(self, img_url):
        """
        อัปเดตแหล่งที่มาของรูปภาพ QR Code บนหน้าจอ
        """
        self.qr_image.source = img_url
        self.qr_image.reload() # บังคับโหลดรูปภาพใหม่

    def update_timer(self, dt):
        """
        อัปเดต Timer นับถอยหลังบนหน้าจอ
        """
        time_elapsed = time.time() - self.payment_start_time
        # ใช้ค่า payment_timeout_seconds จาก APP_CONFIG
        time_remaining = max(0, APP_CONFIG["payment_timeout_seconds"] - int(time_elapsed))
        self.timer_label.text = f'เวลาเหลือ: {time_remaining} วินาที'

        if time_remaining <= 0:
            self.payment_timer.cancel() # หยุด Timer
            if self.check_status_event:
                self.check_status_event.cancel() # หยุดการตรวจสอบสถานะ
            print("[Payment] Payment time expired.")
            self.show_error_popup("หมดเวลา", "หมดเวลาชำระเงิน กรุณาลองใหม่อีกครั้ง")
            self.manager.current = 'amount_selection' # กลับไปหน้าเลือกจำนวนเงิน

    def _check_payment_status(self, dt):
        """
        ตรวจสอบสถานะการชำระเงินผ่าน API (ทำงานในเธรดแยก)
        """
        if not self.ref_id or not self.check_url:
            print("[Payment] No refId or check_url to check status.")
            return

        threading.Thread(target=self.__check_payment_status_async).start()

    def __check_payment_status_async(self):
        """
        ฟังก์ชันหลักสำหรับตรวจสอบสถานะการชำระเงินแบบ Async
        """
        try:
            print(f"[Payment] Checking payment status for {self.ref_id} at {self.check_url}")
            response = requests.get(self.check_url, timeout=5) # เพิ่ม timeout
            response.raise_for_status()
            data = response.json()
            
            print(f"[Payment] Check status response: {json.dumps(data, indent=2)}")

            if data and data.get('status') == 'success':
                # ชำระเงินสำเร็จ
                Clock.schedule_once(lambda dt: self.handle_payment_success(data.get('amount')))
            elif data and data.get('status') == 'cancel':
                # การชำระเงินถูกยกเลิก (จาก API หรือผู้ใช้)
                Clock.schedule_once(lambda dt: self.handle_payment_cancelled())
            # ถ้าเป็น 'pedding' ก็รอตรวจสอบต่อไป
            
        except requests.exceptions.Timeout:
            print(f"[Payment] Status check timed out for {self.ref_id}.")
        except requests.exceptions.RequestException as e:
            print(f"[Payment] Network or API error during status check: {e}")
        except json.JSONDecodeError as e:
            print(f"[Payment] JSON Decode Error during status check: {e}")
        except Exception as e:
            print(f"[Payment] An unexpected error occurred during status check: {e}")

    def handle_payment_success(self, paid_amount):
        """
        จัดการเมื่อชำระเงินสำเร็จ
        """
        print(f"[Payment] Payment successful! Amount paid: {paid_amount}")
        # หยุด Timer และการตรวจสอบสถานะ
        if self.payment_timer:
            self.payment_timer.cancel()
        if self.check_status_event:
            self.check_status_event.cancel()
        
        # คำนวณจำนวนเหรียญที่จะจ่าย
        try:
            # ใช้ค่า coin_per_baht_ratio จาก APP_CONFIG
            num_coins_to_dispense = int(float(paid_amount) * APP_CONFIG["coin_per_baht_ratio"])
            print(f"[Payment] Dispensing {num_coins_to_dispense} coins for {paid_amount} Baht.")
            # เรียกฟังก์ชันจ่ายเหรียญจาก coin_dispenser_gpio module
            c_gpio.start_dispensing(num_coins_to_dispense) 
            
            # ไปหน้าขอบคุณ
            self.manager.get_screen('thank_you').set_message(f'ชำระเงินสำเร็จ {paid_amount} บาท\nกำลังจ่ายเหรียญ {num_coins_to_dispense} เหรียญ')
            self.manager.current = 'thank_you'

        except ValueError:
            print(f"[Payment] Error converting paid_amount '{paid_amount}' to float.")
            self.show_error_popup("Error", "ไม่สามารถประมวลผลจำนวนเงินที่จ่ายได้")
            self.manager.current = 'amount_selection'
        

    def handle_payment_cancelled(self):
        """
        จัดการเมื่อการชำระเงินถูกยกเลิก
        """
        print("[Payment] Payment cancelled by API.")
        self.show_error_popup("การชำระเงินถูกยกเลิก", "การชำระเงินถูกยกเลิก กรุณาลองใหม่อีกครั้ง")
        self.manager.current = 'amount_selection'

    def cancel_payment(self, instance):
        """
        ผู้ใช้กดปุ่มยกเลิกการชำระเงิน
        """
        print("[Payment] User cancelled payment.")
        self.manager.current = 'amount_selection'

    def show_error_popup(self, title, message):
        """
        แสดง Popup ข้อความแจ้งเตือน
        """
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(25), halign='center', valign='middle'))
        close_button = Button(text='ตกลง', size_hint=(1, 0.3), font_size=dp(20))
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, 
                      content=popup_layout, 
                      size_hint=(0.7, 0.4), 
                      auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()


class ThankYouScreen(Screen):
    """
    หน้าจอขอบคุณ
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'thank_you'
        self.message_label = Label(text='ขอบคุณ!', font_size=dp(60), halign='center', valign='middle')
        self.add_widget(self.message_label)

    def set_message(self, message):
        self.message_label.text = message

    def on_enter(self):
        # ตั้งเวลา 5 วินาทีแล้วกลับไปหน้าเริ่มต้น
        Clock.schedule_once(self.go_back_to_welcome, 5)

    def go_back_to_welcome(self, dt):
        self.manager.current = 'welcome'

class SettingsScreen(Screen):
    """
    หน้าจอตั้งค่า ที่มีระบบรหัสผ่านและ On-screen Keyboard
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self.password_popup = None 

        self.settings_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.settings_layout.add_widget(Label(text='หน้าจอตั้งค่า', font_size=dp(40), size_hint_y=0.15))

        shutdown_app_button = Button(text='ปิดแอปพลิเคชัน', 
                                     font_size=dp(30), 
                                     background_color=(0.8, 0.2, 0.2, 1),
                                     size_hint_y=0.1)
        shutdown_app_button.bind(on_release=self.shutdown_application)
        self.settings_layout.add_widget(shutdown_app_button)
        
        # Input fields สำหรับการตั้งค่าต่างๆ
        self.settings_layout.add_widget(Label(text='API Key:', font_size=dp(25), size_hint_y=None, height=dp(30), halign='left', text_size=(Window.width - dp(40), None)))
        self.api_key_input = TextInput(multiline=False, font_size=dp(25), size_hint_y=None, height=dp(50))
        self.settings_layout.add_widget(self.api_key_input)

        self.settings_layout.add_widget(Label(text='Username:', font_size=dp(25), size_hint_y=None, height=dp(30), halign='left', text_size=(Window.width - dp(40), None)))
        self.username_input = TextInput(multiline=False, font_size=dp(25), size_hint_y=None, height=dp(50))
        self.settings_layout.add_widget(self.username_input)

        self.settings_layout.add_widget(Label(text='Admin Password:', font_size=dp(25), size_hint_y=None, height=dp(30), halign='left', text_size=(Window.width - dp(40), None)))
        self.admin_password_input = TextInput(multiline=False, password=True, font_size=dp(25), size_hint_y=None, height=dp(50))
        self.settings_layout.add_widget(self.admin_password_input)

        self.settings_layout.add_widget(Label(text='Coin per Baht Ratio (e.g., 10 for 10 baht/coin):', font_size=dp(25), size_hint_y=None, height=dp(30), halign='left', text_size=(Window.width - dp(40), None)))
        self.coin_ratio_input = TextInput(input_type='number', multiline=False, font_size=dp(25), size_hint_y=None, height=dp(50))
        self.settings_layout.add_widget(self.coin_ratio_input)

        self.settings_layout.add_widget(Label(text='Payment Timeout (seconds):', font_size=dp(25), size_hint_y=None, height=dp(30), halign='left', text_size=(Window.width - dp(40), None)))
        self.payment_timeout_input = TextInput(input_type='number', multiline=False, font_size=dp(25), size_hint_y=None, height=dp(50))
        self.settings_layout.add_widget(self.payment_timeout_input)
        
        save_button = Button(text='บันทึกการตั้งค่า', font_size=dp(30), background_color=(0.2, 0.7, 0.2, 1), size_hint_y=0.1)
        save_button.bind(on_release=self.save_settings)
        self.settings_layout.add_widget(save_button)

        back_button = Button(text='ย้อนกลับ', font_size=dp(30), background_color=(0.8, 0.4, 0.2, 1), size_hint_y=0.1)
        back_button.bind(on_release=self.go_back_to_welcome)
        self.settings_layout.add_widget(back_button)

        self.add_widget(self.settings_layout) 
        self.settings_layout.opacity = 0
        self.settings_layout.disabled = True

    def show_password_popup(self, manager_instance):
        """
        แสดง Popup สำหรับใส่รหัสผ่าน พร้อม On-screen Keyboard
        """
        self.manager_instance = manager_instance

        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text='ป้อนรหัสผ่าน Admin:', font_size=dp(30)))
        
        # ช่องใส่รหัสผ่าน - ตั้งค่า readonly=True เพื่อให้รับ input จาก keyboard เราเท่านั้น
        self.password_input = TextInput(password=True, multiline=False, font_size=dp(30), 
                                        size_hint_y=None, height=dp(50), 
                                        readonly=True, # ทำให้ไม่สามารถพิมพ์จากคีย์บอร์ดภายนอกได้
                                        input_type='number', # บอกว่าเป็นช่องใส่ตัวเลข (ช่วยเรื่องคีย์บอร์ดระบบ)
                                        input_filter='int') # กรองให้รับแต่ตัวเลข
        popup_layout.add_widget(self.password_input)

        # On-screen Numeric Keyboard
        keypad_grid = GridLayout(cols=3, spacing=dp(5), size_hint_y=0.7)
        keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'Clear', '0', 'Delete']
        for key in keys:
            btn = Button(text=key, font_size=dp(35))
            btn.bind(on_release=self.on_key_press)
            keypad_grid.add_widget(btn)
        
        popup_layout.add_widget(keypad_grid)

        # ปุ่ม ตกลง และ ยกเลิก
        button_layout = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        ok_button = Button(text='ตกลง', font_size=dp(25))
        ok_button.bind(on_release=self.check_password)
        button_layout.add_widget(ok_button)
        
        cancel_button = Button(text='ยกเลิก', font_size=dp(25))
        cancel_button.bind(on_release=lambda x: self.password_popup.dismiss())
        button_layout.add_widget(cancel_button)
        
        popup_layout.add_widget(button_layout)

        self.password_popup = Popup(title='Admin Access', 
                                    content=popup_layout, 
                                    size_hint=(0.8, 0.9), # เพิ่มขนาด popup เพื่อรองรับ keyboard
                                    auto_dismiss=False)
        self.password_popup.open()
        self.manager.current = 'settings'

    def on_key_press(self, instance):
        """
        จัดการการกดปุ่มบน On-screen Keyboard
        """
        key = instance.text
        if key == 'Clear':
            self.password_input.text = ''
        elif key == 'Delete':
            self.password_input.text = self.password_input.text[:-1]
        else:
            self.password_input.text += key

    def check_password(self, instance):
        """
        ตรวจสอบรหัสผ่านที่ผู้ใช้ป้อนจากช่อง TextInput
        """
        if self.password_input.text == APP_CONFIG["admin_password"]:
            self.password_popup.dismiss()
            self.on_enter_admin_mode()
        else:
            self.show_error_popup("รหัสผ่านผิด", "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
            self.password_input.text = '' # ล้างช่องใส่รหัสผ่าน

    def on_enter_admin_mode(self):
        """
        เมื่อเข้าสู่โหมด Admin สำเร็จ: แสดง UI การตั้งค่าและโหลดค่าปัจจุบัน
        """
        print("[Settings] Admin mode entered successfully.")
        # โหลดค่าล่าสุดจาก APP_CONFIG มาแสดงใน Input fields
        self.api_key_input.text = APP_CONFIG["api_key"]
        self.username_input.text = APP_CONFIG["username"]
        self.admin_password_input.text = APP_CONFIG["admin_password"] 
        self.coin_ratio_input.text = str(APP_CONFIG["coin_per_baht_ratio"])
        self.payment_timeout_input.text = str(APP_CONFIG["payment_timeout_seconds"])

        self.settings_layout.opacity = 1 # ทำให้ UI ตั้งค่าปรากฏ
        self.settings_layout.disabled = False # เปิดการใช้งาน UI

    def on_leave(self):
        """
        เมื่อออกจากหน้า Settings: ซ่อน UI การตั้งค่าและล้างช่องใส่รหัสผ่าน
        """
        self.settings_layout.opacity = 0
        self.settings_layout.disabled = True
        self.password_input.text = '' # ล้างรหัสผ่านเมื่อออก

    def shutdown_application(self, instance):
        """
        ฟังก์ชันปิดแอปพลิเคชัน
        """
        print("[Settings] Shutting down application...")
        App.get_running_app().stop() # สั่งให้ Kivy App หยุดทำงาน
        # หากต้องการปิด Raspberry Pi ด้วย (ต้องตั้งค่า sudoers ให้สิทธิ์ NOPASSWD)
        # import os
        # os.system("sudo shutdown -h now") 
        
    def save_settings(self, instance):
        """
        บันทึกค่าการตั้งค่าจาก Input fields ลงใน APP_CONFIG และไฟล์ JSON
        """
        try:
            APP_CONFIG["api_key"] = self.api_key_input.text
            APP_CONFIG["username"] = self.username_input.text
            APP_CONFIG["admin_password"] = self.admin_password_input.text
            
            # ตรวจสอบว่าค่าที่ใส่เป็นตัวเลข
            APP_CONFIG["coin_per_baht_ratio"] = int(self.coin_ratio_input.text)
            APP_CONFIG["payment_timeout_seconds"] = int(self.payment_timeout_input.text)
            
            save_config() # เรียกฟังก์ชันบันทึกไปที่ไฟล์
            self.show_error_popup("บันทึกการตั้งค่า", "บันทึกข้อมูลเรียบร้อย")
        except ValueError:
            self.show_error_popup("ข้อผิดพลาด", "โปรดป้อนตัวเลขสำหรับ Coin Ratio และ Payment Timeout")
        except Exception as e:
            self.show_error_popup("ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่าได้: {e}")

    def go_back_to_welcome(self, instance):
        """
        กลับไปหน้า Welcome Screen
        """
        self.manager.current = 'welcome'

    def show_error_popup(self, title, message):
        """
        แสดง Popup ข้อความแจ้งเตือนข้อผิดพลาดหรือข้อมูลทั่วไป
        """
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(25), halign='center', valign='middle'))
        close_button = Button(text='ตกลง', size_hint=(1, 0.3), font_size=dp(20))
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, 
                      content=popup_layout, 
                      size_hint=(0.7, 0.4), 
                      auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()


class CoinMachineApp(App):
    """
    คลาสหลักของแอปพลิเคชัน Kivy
    """
    # ตัวแปรสำหรับ Debounce การแตะหน้าจอ
    _last_touch_time = 0
    TOUCH_DEBOUNCE_TIME = 0.15 # วินาที (150 มิลลิวินาที) - ปรับค่านี้ตามความเหมาะสม

    def build(self):
        # โหลดการตั้งค่าจากไฟล์ JSON เมื่อแอปเริ่มต้น
        load_config() 
        
        # ตั้งค่าพื้นหลังหน้าต่าง Kivy เป็นสีดำ
        Window.clearcolor = (0, 0, 0, 1) 

        # สร้าง ScreenManager เพื่อจัดการการเปลี่ยนหน้าจอ
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(AmountSelectionScreen(name='amount_selection'))
        sm.add_widget(PaymentScreen(name='payment'))
        sm.add_widget(ThankYouScreen(name='thank_you'))
        sm.add_widget(SettingsScreen(name='settings')) 

        sm.current = 'welcome' # กำหนดหน้าเริ่มต้น
        return sm

    def on_touch_down(self, touch):
        """
        Override เมธอด on_touch_down เพื่อจัดการ Debounce การแตะหน้าจอ
        """
        current_time = time.time()
        if current_time - self._last_touch_time < self.TOUCH_DEBOUNCE_TIME:
            # ถ้าการแตะเกิดขึ้นเร็วเกินไป ถือว่าเป็น Bounce ให้ละทิ้ง Event นี้
            print(f"[Debounce] Touch ignored due to debounce. Time diff: {current_time - self._last_touch_time:.3f}s")
            return True # คืนค่า True เพื่อบอกว่า Event ถูกจัดการแล้ว (และไม่ส่งต่อ)
        
        # ถ้าไม่ใช่ Bounce ให้ประมวลผล Event ต่อไปตามปกติ
        self._last_touch_time = current_time
        return super().on_touch_down(touch)


if __name__ == '__main__':
    # การเริ่มต้นโมดูล GPIO
    # c_gpio (coin_dispenser_gpio.py) จะทำการตั้งค่าขา GPIO และเริ่มเธรดที่เกี่ยวข้องโดยอัตโนมัติเมื่อถูก import
    print("GPIO module imported and initialized.")
    
    # รันแอปพลิเคชัน Kivy
    try:
        CoinMachineApp().run()
    except KeyboardInterrupt:
        # ดักจับ Ctrl+C เพื่อให้โปรแกรมสามารถปิดอย่างสวยงาม
        print("\nApplication interrupted by user (Ctrl+C).")
    finally:
        # การทำความสะอาด GPIO จะถูกจัดการโดยโมดูล coin_dispenser_gpio เอง
        # หรือโดย gpiozero's automatic cleanup เมื่อโปรแกรมจบ
        print("Application stopped. GPIO cleanup handled by coin_dispenser_gpio module.")
