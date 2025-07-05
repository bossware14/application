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
# mkdir -p /home/pi5/.config/autostart/
# nano /home/pi5/.config/autostart/kiosk_app.desktop
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
# แก้ไขชื่อไฟล์ฟอนต์ให้ถูกต้องตามที่คุณมี
FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'NotoSansThai-Regular.ttf') 
if not os.path.exists(FONT_PATH):
    print(f"Error: Font file not found at {FONT_PATH}. Thai characters may not display correctly.")
    LabelBase.register(name='Roboto', fn_regular='DejaVuSans.ttf' if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') else 'FreeSans.ttf')
else:
    LabelBase.register(name='Roboto', fn_regular=FONT_PATH)

import requests
import json
import threading
import time

# --- Import GPIO Control Module ---
import coin_dispenser_gpio as c_gpio 

# --- Global Configuration ---
CONFIG_FILE = 'config.json' 
APP_CONFIG = {
    "api_key": "F8C04-06726831FD",
    "username": "coin_matchine_01",
    "admin_password": "112233",
    "coin_per_baht_ratio": 0.1,
    "payment_timeout_seconds": 120,
    "image_welcome_url" : "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSF-ymPuon8o9JiW5SKog_sIePZmkra_0FNEMXN6UooOBJ44neWddPuZws&s=10",
    "image_qrcode_url" : "https://image-charts.com/chart?chs=200x200&cht=qr&choe=UTF-8&chl=",
    "amounts":[10, 20, 30,50],
    "payment":[20, 30, 50, 100]
}

BASE_PAYMENT_URL = "https://payment.all123th.com/api-pay"
CHECK_STATUS_BASE_URL = "https://api.all123th.com/payment-swiftpay/"

# --- Fullscreen Setup ---
Window.fullscreen = 'auto'

# --- Config Management Functions ---
def load_config():
    global APP_CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                APP_CONFIG.update(loaded_config)
            print(f"[Config] Config loaded from {CONFIG_FILE}")
        except json.JSONDecodeError:
            print(f"[Config] Error decoding JSON from {CONFIG_FILE}. Using default config.")
        except Exception as e:
            print(f"[Config] An error occurred while loading config: {e}. Using default config.")
    else:
        print(f"[Config] Config file {CONFIG_FILE} not found. Using default config.")
    save_config() 

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(APP_CONFIG, f, indent=4)
        print(f"[Config] Config saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"[Config] An error occurred while saving config: {e}")

from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage # สำหรับโหลด texture รูปภาพ
# ... (ส่วน import อื่นๆ ของคุณ) ...

# สมมติว่ามีไฟล์รูปภาพพื้นหลัง
BACKGROUND_IMAGE_PATH = os.path.join(os.path.dirname(__file__), 'images', 'background.jpg') 

class WelcomeScreen(Screen):
    _last_click_time = 0 # เพิ่มตัวแปรสำหรับ debounce เฉพาะปุ่ม
    BUTTON_DEBOUNCE_TIME = 0.2 # กำหนดเวลา debounce สำหรับปุ่มนี้

    def __init__(self, **kwargs):   
        super().__init__(**kwargs)
        self.name = 'welcome'
        
        layout = BoxLayout(orientation='vertical')
        
        self.ad_image = AsyncImage(source='images/ads.jpg', size_hint=(1,1))
        layout.add_widget(self.ad_image)

        start_button = Button(text='แตะเพื่อเริ่ม', font_size=dp(30), size_hint=(1, 0.2), background_color=(0.2, 0.7, 0.2, 1))
        start_button.bind(on_release=self.go_to_amount_selection)
        layout.add_widget(start_button)

        admin_button = Button(text='Admin', font_size=dp(18), size_hint=(1, 0.1), background_color=(0.5, 0.5, 0.5, 1))
        admin_button.bind(on_release=self.go_to_admin_auth)
        layout.add_widget(admin_button)

        self.add_widget(layout)

    def go_to_amount_selection(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            return True
        self._last_click_time = current_time # อัปเดตเวลาการคลิก
        print("[WelcomeScreen] Going to Amount Selection.")
        self.manager.current = 'amount_selection'

    def go_to_amount_selection(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            return True
        self._last_click_time = current_time
        self.manager.current = 'amount_selection'

    def go_to_admin_auth(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            return True
        self._last_click_time = current_time
        self.manager.current = 'admin_auth'


class AmountSelectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'amount_selection'
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        layout.add_widget(Label(text='กรุณาเลือกจำนวนเงิน', font_size=dp(40), size_hint_y=0.2,color=(0,0,0)))
        button_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.7)
        amounts = [20, 30, 50, 100]
        for amount in amounts:
            btn = Button(text=f'{amount} บาท', font_size=dp(40), background_color=(0.2, 0.5, 0.8, 1))
            btn.bind(on_release=lambda x, a=amount: self.select_amount(a))
            button_grid.add_widget(btn)
        layout.add_widget(button_grid)
        back_button = Button(text='ย้อนกลับ', font_size=dp(25), size_hint_y=0.1, background_color=(0.8, 0.4, 0.2, 1))
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
    _last_click_time = 0 # เพิ่มตัวแปรสำหรับ debounce เฉพาะปุ่ม
    BUTTON_DEBOUNCE_TIME = 0.2 # กำหนดเวลา debounce สำหรับปุ่มนี้

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'payment'
        
        self.payment_amount = 0
        self.ref_id = None
        self.check_url = None
        self.payment_timer = None
        self.check_status_event = None

        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
        
        self.amount_label = Label(text='จำนวนเงิน: 0 บาท', font_size=dp(35), size_hint_y=0.15,color=(0,0,0))
        layout.add_widget(self.amount_label)

        self.qr_image = AsyncImage(source='', size_hint=(1, 0.6))
        layout.add_widget(self.qr_image)

        self.timer_label = Label(text=f'เวลาเหลือ: {APP_CONFIG["payment_timeout_seconds"]} วินาที', font_size=dp(30), size_hint_y=0.1,color=(0,0,0))
        layout.add_widget(self.timer_label)

        cancel_button = Button(text='ยกเลิก', font_size=dp(25), size_hint_y=0.15, background_color=(0.8, 0.2, 0.2, 1))
        cancel_button.bind(on_release=self.cancel_payment)
        layout.add_widget(cancel_button)

        self.add_widget(layout)
    
    def set_payment_amount(self, amount):
        self.payment_amount = amount
        self.amount_label.text = f'จำนวนเงิน: {amount} บาท'
        self.timer_label.text = f'เวลาเหลือ: {APP_CONFIG["payment_timeout_seconds"]} วินาที' 

    def on_enter(self):
        self.qr_image.source = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQbF0JgqiEWN6wFHxWQCrIfllBR_qsNVq-1Cg&usqp=CAU'
        self.qr_image.reload()
        self.start_payment_process()

    def on_leave(self):
        if self.payment_timer:
            self.payment_timer.cancel()
        if self.check_status_event:
            self.check_status_event.cancel()
        self.ref_id = None
        self.check_url = None
        print("[Payment] Payment process stopped.")

    def start_payment_process(self):
        print(f"Payment: Requesting QR code for amount: {self.payment_amount}")
        self.payment_start_time = time.time()
        if self.payment_timer:
            self.payment_timer.cancel() 
        self.payment_timer = Clock.schedule_interval(self.update_timer, 1)
        threading.Thread(target=self._request_qr_code).start()

    def _request_qr_code(self):
        try:
            url = f"{BASE_PAYMENT_URL}?amount={self.payment_amount}&secretKey={APP_CONFIG['api_key']}&username={APP_CONFIG['username']}"
            print(f"Payment: Calling API: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            print(f"Payment: API Response: {json.dumps(data, indent=2)}")

            if data and data.get('status') ==  "padding":
                qr_img_url = data.get('img')
                self.ref_id = data.get('refId')
                self.check_url = f"{CHECK_STATUS_BASE_URL}{self.ref_id}?type=json"

                if qr_img_url:
                    Clock.schedule_once(lambda dt: self.update_qr_image(qr_img_url))
                    if self.check_status_event:
                        self.check_status_event.cancel()
                    self.check_status_event = Clock.schedule_interval(self._check_payment_status, 3)
                else:
                    print("Payment: Error: No QR image URL in response.")
                    Clock.schedule_once(lambda dt: self.show_error_popup("QR Code Error", "ไม่สามารถสร้าง QR Code ได้ (URL รูปภาพไม่พบ)"))
            else:
                print(f"Payment: API response status not pedding: {data.get('status')}")
                Clock.schedule_once(lambda dt: self.show_error_popup("API Error", "การสร้าง QR Code ล้มเหลว (สถานะไม่ถูกต้อง)"))

        except requests.exceptions.Timeout:
            print(f"Payment: API request timed out.")
            Clock.schedule_once(lambda dt: self.show_error_popup("Network Error", "API ตอบสนองช้าเกินไป ลองใหม่อีกครั้ง"))
        except requests.exceptions.RequestException as e:
            print(f"Payment: Network or API error: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Network Error", f"ไม่สามารถเชื่อมต่อ Payment API ได้: {e}"))
        except json.JSONDecodeError as e:
            print(f"Payment: JSON Decode Error: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Data Error", "รูปแบบข้อมูลจาก Payment API ไม่ถูกต้อง"))
        except Exception as e:
            print(f"Payment: An unexpected error occurred: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Error", f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}"))

    def update_qr_image(self, img_url):
        self.qr_image.source = img_url
        self.qr_image.reload()

    def update_timer(self, dt):
        time_elapsed = time.time() - self.payment_start_time
        time_remaining = max(0, APP_CONFIG["payment_timeout_seconds"] - int(time_elapsed))
        self.timer_label.text = f'เวลาเหลือ: {time_remaining} วินาที'

        if time_remaining <= 0:
            self.payment_timer.cancel()
            if self.check_status_event:
                self.check_status_event.cancel()
            print("Payment: Payment time expired.")
            self.show_error_popup("หมดเวลา", "หมดเวลาชำระเงิน กรุณาลองใหม่อีกครั้ง")
            self.manager.current = 'amount_selection'

    def _check_payment_status(self, dt):
        if not self.ref_id or not self.check_url:
            print("Payment: No refId or check_url to check status.")
            return

        threading.Thread(target=self.__check_payment_status_async).start()

    def __check_payment_status_async(self):
        try:
            print(f"Payment: Checking payment status for {self.ref_id} at {self.check_url}")
            response = requests.get(self.check_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            print(f"Payment: Check status response: {json.dumps(data, indent=2)}")

            status_from_api = data.get('status')
            if status_from_api == 'Success':
                paid_amount_str = data.get('data', {}).get('amount')
                Clock.schedule_once(lambda dt: self.handle_payment_success(paid_amount_str))
            elif status_from_api ==  "Pending":
                print(f"Payment: Status is Pedding for {self.ref_id}. Retrying...")
            elif status_from_api == 'Failed':
                Clock.schedule_once(lambda dt: self.handle_payment_failed())
            else:
                print(f"Payment: Unknown status received: {status_from_api} for {self.ref_id}.")
                Clock.schedule_once(lambda dt: self.handle_payment_failed(
                    message=f"เกิดข้อผิดพลาดในการชำระเงิน: {status_from_api}"
                ))
            
        except requests.exceptions.Timeout:
            print(f"Payment: Status check timed out for {self.ref_id}.")
        except requests.exceptions.RequestException as e:
            print(f"Payment: Network or API error during status check: {e}")
        except json.JSONDecodeError as e:
            print(f"Payment: JSON Decode Error during status check: {e}")
        except Exception as e:
            print(f"Payment: An unexpected error occurred during status check: {e}")

    def handle_payment_success(self, paid_amount):
        print(f"Payment: Payment successful! Amount paid: {paid_amount}")
        if self.payment_timer:
            self.payment_timer.cancel()
        if self.check_status_event:
            self.check_status_event.cancel()
        try:
            num_coins_to_dispense = int(float(paid_amount) * APP_CONFIG["coin_per_baht_ratio"])
            print(f"Payment: Dispensing {num_coins_to_dispense} coins for {paid_amount} Baht.")
            c_gpio.start_dispensing(num_coins_to_dispense) 
            
            self.manager.get_screen('thank_you').set_message(f'ชำระเงินสำเร็จ {paid_amount} บาท\nกำลังจ่ายเหรียญ {num_coins_to_dispense} เหรียญ')
            self.manager.current = 'thank_you'

        except ValueError:
            print(f"Payment: Error converting paid_amount '{paid_amount}' to float.")
            self.show_error_popup("Error", "ไม่สามารถประมวลผลจำนวนเงินที่จ่ายได้")
            self.manager.current = 'amount_selection'
        

    def handle_payment_failed(self, message="การชำระเงินไม่สำเร็จ กรุณาลองใหม่อีกครั้ง"):
        print(f"Payment: Payment failed: {message}")
        if self.payment_timer:
            self.payment_timer.cancel()
        if self.check_status_event:
            self.check_status_event.cancel()
        self.show_error_popup("การชำระเงินล้มเหลว", message)
        self.manager.current = 'amount_selection'

    def cancel_payment(self, instance):
        print("Payment: User cancelled payment.")
        self.manager.current = 'amount_selection'

    def show_error_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(25), halign='center', valign='middle'))
        close_button = Button(text='ตกลง', size_hint=(1, 0.3), font_size=dp(20))
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.7, 0.4), auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()


class ThankYouScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'thank_you'
        self.message_label = Label(text='ขอบคุณ!', font_size=dp(50), halign='center', valign='middle',color=(0,0,0))
        self.add_widget(self.message_label)

    def set_message(self, message):
        self.message_label.text = message

    def on_enter(self):
        Clock.schedule_once(self.go_back_to_welcome, 5)

    def go_back_to_welcome(self, dt):
        self.manager.current = 'welcome'

# --- NEW: Admin Authentication Screen ---
class AdminAuthScreen(Screen):
    _last_click_time = 0 # เพิ่มตัวแปรสำหรับ debounce เฉพาะปุ่ม
    BUTTON_DEBOUNCE_TIME = 0.1 # กำหนดเวลา debounce สำหรับปุ่มนี้

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'admin_auth'
        
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
        
        layout.add_widget(Label(text='ป้อนรหัสผ่าน Admin:', font_size=dp(35), size_hint_y=0.2))
        
        self.password_input = TextInput(password=True, multiline=False, font_size=dp(28), 
                                        size_hint_y=None, height=dp(45), 
                                        readonly=True, 
                                        input_type='number', 
                                        input_filter='int')
        layout.add_widget(self.password_input)

        keypad_grid = GridLayout(cols=3, spacing=dp(4), size_hint_y=0.6)
        keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'Clear', '0', 'Delete']
        for key in keys:
            btn = Button(text=key, font_size=dp(30))
            btn.bind(on_release=self.on_key_press)
            keypad_grid.add_widget(btn)
        
        layout.add_widget(keypad_grid)

        button_layout = BoxLayout(size_hint_y=0.2, spacing=dp(8))
        ok_button = Button(text='ตกลง', font_size=dp(25), background_color=(0.2, 0.7, 0.2, 1))
        ok_button.bind(on_release=self.check_password)
        button_layout.add_widget(ok_button)
        
        cancel_button = Button(text='ยกเลิก', font_size=dp(25), background_color=(0.8, 0.4, 0.2, 1))
        cancel_button.bind(on_release=self.go_back_to_welcome)
        button_layout.add_widget(cancel_button)
        
        layout.add_widget(button_layout)

        self.add_widget(layout)

    def on_key_press(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            return True# ไม่ทำอะไรต่อ ถ้ายังอยู่ในช่วง debounce
        
        self._last_click_time = current_time # อัปเดตเวลาการคลิก

        key = instance.text
        if key == 'Clear':
            self.password_input.text = ''
        elif key == 'Delete':
            self.password_input.text = self.password_input.text[:-1]
        else:
            self.password_input.text += key

    def check_password(self, instance):
        current_time = time.time()
        #

        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            #
            return True# ไม่ทำอะไรต่อ ถ้ายังอยู่ในช่วง debounce
        
        self._last_click_time = current_time # อัปเดตเวลาการคลิก

        if self.password_input.text == APP_CONFIG["admin_password"]:
            print("AdminAuthScreen: Password correct. Entering Admin Panel.")
            self.password_input.text = ''
            self.manager.current = 'admin_panel'
        else:
            print("AdminAuthScreen: Incorrect password entered.")
            self.show_error_popup("รหัสผ่านผิด", "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
            self.password_input.text = ''

    def go_back_to_welcome(self, instance):
        self.password_input.text = ''
        self.manager.current = 'welcome'
        current_time = time.time()
        

        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            
            return True# ไม่ทำอะไรต่อ ถ้ายังอยู่ในช่วง debounce
        
        self._last_click_time = current_time # อัปเดตเวลาการคลิก

    def show_error_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(22), halign='center', valign='middle'))
        close_button = Button(text='ตกลง', size_hint=(1, 0.3), font_size=dp(18))
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.7, 0.4), auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()


# --- RENAMED: Admin Panel Screen (formerly SettingsScreen) ---
class AdminPanelScreen(Screen):
    _last_click_time = 0 # เพิ่มตัวแปรสำหรับ debounce เฉพาะปุ่ม
    BUTTON_DEBOUNCE_TIME = 0.1 # กำหนดเวลา debounce สำหรับปุ่มนี้

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'admin_panel'
        
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(5))
        layout.add_widget(Label(text='หน้าจอตั้งค่า Admin', font_size=dp(35), size_hint_y=0.1))
        # --- ส่วนของปุ่มควบคุมหลัก (GridLayout) ---
        control_buttons_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.2) # 2 คอลัมน์
        
        shutdown_app_button = Button(text='ปิดแอปพลิเคชัน', 
                                     font_size=dp(25), 
                                     background_color=(0.8, 0.2, 0.2, 1))
        shutdown_app_button.bind(on_release=self.shutdown_application)
        control_buttons_grid.add_widget(shutdown_app_button)
        
        save_button = Button(text='บันทึกการตั้งค่า', font_size=dp(25), background_color=(0.2, 0.7, 0.2, 1))
        save_button.bind(on_release=self.save_settings)
        control_buttons_grid.add_widget(save_button)

        # --- NEW: ปุ่มสำหรับไปหน้าเพิ่มเหรียญ ---
        add_coins_button = Button(text='เพิ่มเหรียญ', font_size=dp(25), background_color=(0.2, 0.5, 0.8, 1))
        add_coins_button.bind(on_release=self.go_to_add_money_screen)
        control_buttons_grid.add_widget(add_coins_button)

        back_button = Button(text='ย้อนกลับ', font_size=dp(25), background_color=(0.8, 0.4, 0.2, 1))
        back_button.bind(on_release=self.go_back_to_welcome)
        control_buttons_grid.add_widget(back_button)

        layout.add_widget(control_buttons_grid)
        # --- จบส่วนของปุ่มควบคุม ---

        # Input fields สำหรับการตั้งค่าต่างๆ (ส่วนนี้ยังอยู่ใน BoxLayout หลัก)
        self.api_key_label = Label(text='API Key:', font_size=dp(20), size_hint_y=None, height=dp(25), halign='left', text_size=(Window.width - dp(30), None))
        layout.add_widget(self.api_key_label)
        self.api_key_input = TextInput(multiline=False, font_size=dp(20), size_hint_y=None, height=dp(40))
        layout.add_widget(self.api_key_input)

        self.username_label = Label(text='Username:', font_size=dp(20), size_hint_y=None, height=dp(25), halign='left', text_size=(Window.width - dp(30), None))
        layout.add_widget(self.username_label)
        self.username_input = TextInput(multiline=False, font_size=dp(20), size_hint_y=None, height=dp(40))
        layout.add_widget(self.username_input)

        self.admin_password_label = Label(text='Admin Password:', font_size=dp(20), size_hint_y=None, height=dp(25), halign='left', text_size=(Window.width - dp(30), None))
        layout.add_widget(self.admin_password_label)
        self.admin_password_input = TextInput(multiline=False, password=True, font_size=dp(20), size_hint_y=None, height=dp(40))
        layout.add_widget(self.admin_password_input)

        self.coin_ratio_label = Label(text='Coin per Baht Ratio (e.g., 10 for 10 baht/coin):', font_size=dp(20), size_hint_y=None, height=dp(25), halign='left', text_size=(Window.width - dp(30), None))
        layout.add_widget(self.coin_ratio_label)
        self.coin_ratio_input = TextInput(input_type='number', multiline=False, font_size=dp(20), size_hint_y=None, height=dp(40))
        layout.add_widget(self.coin_ratio_input)

        self.payment_timeout_label = Label(text='Payment Timeout (seconds):', font_size=dp(20), size_hint_y=None, height=dp(25), halign='left', text_size=(Window.width - dp(30), None))
        layout.add_widget(self.payment_timeout_label)
        self.payment_timeout_input = TextInput(input_type='number', multiline=False, font_size=dp(20), size_hint_y=None, height=dp(40))
        layout.add_widget(self.payment_timeout_input)
        
        self.add_widget(layout) 
        
    def on_enter(self):
        print("AdminPanelScreen: Entered.")
        self.api_key_input.text = APP_CONFIG["api_key"]
        self.username_input.text = APP_CONFIG["username"]
        self.admin_password_input.text = APP_CONFIG["admin_password"] 
        self.coin_ratio_input.text = str(APP_CONFIG["coin_per_baht_ratio"])
        self.payment_timeout_input.text = str(APP_CONFIG["payment_timeout_seconds"])

    def on_leave(self):
        print("AdminPanelScreen: Leaving.")
        
    def shutdown_application(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            #
            return True# ไม่ทำอะไรต่อ ถ้ายังอยู่ในช่วง debounce
        
        self._last_click_time = current_time # อัปเดตเวลาการคลิก

        print("AdminPanelScreen: Shutting down application...")
        App.get_running_app().stop()
        import os
        os.system("sudo reboot") 

    def save_settings(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            return True# ไม่ทำอะไรต่อ ถ้ายังอยู่ในช่วง debounce
        self._last_click_time = current_time # อัปเดตเวลาการคลิก
        try:
            APP_CONFIG["api_key"] = self.api_key_input.text
            APP_CONFIG["username"] = self.username_input.text
            APP_CONFIG["admin_password"] = self.admin_password_input.text
            
            APP_CONFIG["coin_per_baht_ratio"] = int(self.coin_ratio_input.text)
            APP_CONFIG["payment_timeout_seconds"] = int(self.payment_timeout_input.text)
            
            save_config()
            self.show_error_popup("บันทึกการตั้งค่า", "บันทึกข้อมูลเรียบร้อย")
        except ValueError:
            self.show_error_popup("ข้อผิดพลาด", "โปรดป้อนตัวเลขสำหรับ Coin Ratio และ Payment Timeout")
        except Exception as e:
            self.show_error_popup("ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่าได้: {e}")

    def go_back_to_welcome(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            return True# ไม่ทำอะไรต่อ ถ้ายังอยู่ในช่วง debounce
        self._last_click_time = current_time # อัปเดตเวลาการคลิก
        self.manager.current = 'welcome'

    def go_to_add_money_screen(self, instance):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            #
            return True# ไม่ทำอะไรต่อ ถ้ายังอยู่ในช่วง debounce
        
        self._last_click_time = current_time # อัปเดตเวลาการคลิก
        self.manager.current = 'add_money_admin' # เปลี่ยนไปหน้าใหม่

    def show_error_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(25), halign='center', valign='middle'))
        close_button = Button(text='ตกลง', size_hint=(1, 0.3), font_size=dp(20))
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.7, 0.4), auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()

# --- NEW: Add Money Screen for Admin ---
class AddMoneyScreen(Screen):
    _last_click_time = 0 # เพิ่มตัวแปรสำหรับ debounce เฉพาะปุ่ม
    BUTTON_DEBOUNCE_TIME = 0.2 # กำหนดเวลา debounce สำหรับปุ่มนี้

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'add_money_admin'
        
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        layout.add_widget(Label(text='Admin: เลือกจำนวนเงินที่ต้องการเพิ่ม', font_size=dp(35), size_hint_y=0.2))
        
        button_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=0.7)
        amounts = [10, 20, 30,50] # ตัวเลือกจำนวนเงิน
        for amount in amounts:
            btn = Button(text=f'{amount} บาท', font_size=dp(40), background_color=(0.2, 0.5, 0.8, 1))
            btn.bind(on_release=lambda x, a=amount: self.dispense_coins_for_amount(a))
            button_grid.add_widget(btn)
        
        # เพิ่มปุ่ม Dummy เพื่อให้มี 2 คอลัมน์ (ถ้ามีแค่ 3 ปุ่ม)
        if len(amounts) % 2 != 0: # ถ้าจำนวนปุ่มเป็นเลขคี่
            button_grid.add_widget(Label(text='', size_hint=(1,1))) # ปุ่มว่างเพื่อจัดคอลัมน์ให้สมมาตร

        layout.add_widget(button_grid)
        
        back_button = Button(text='ย้อนกลับ', font_size=dp(25), size_hint_y=0.1, background_color=(0.8, 0.4, 0.2, 1))
        back_button.bind(on_release=self.go_back_to_admin_panel)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def dispense_coins_for_amount(self, amount_baht):
        current_time = time.time()
        if current_time - self._last_click_time < self.BUTTON_DEBOUNCE_TIME:
            return True 
        self._last_click_time = current_time

        num_coins = int(amount_baht * APP_CONFIG["coin_per_baht_ratio"])
        print(f"Admin: Dispensing {num_coins} coins for {amount_baht} Baht (Admin Manual Add).")
        c_gpio.start_dispensing(num_coins)
        self.show_info_popup("จ่ายเหรียญ", f"กำลังจ่ายเหรียญ {num_coins} เหรียญ สำหรับ {amount_baht} บาท")
        # อาจจะกลับไปหน้า Admin Panel โดยอัตโนมัติหลังจากจ่ายเหรียญ
        Clock.schedule_once(lambda dt: self.go_back_to_admin_panel(), 3) # กลับใน 3 วินาที

    def go_back_to_admin_panel(self, instance=None): # instance=None เพื่อรองรับการเรียกจาก Clock.schedule_once
        self.manager.current = 'admin_panel'

    def show_info_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(25), halign='center', valign='middle'))
        close_button = Button(text='ตกลง', size_hint=(1, 0.3), font_size=dp(20))
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.7, 0.4), auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()


class CoinMachineApp(App):
    _last_touch_time = 0
    TOUCH_DEBOUNCE_TIME = 0.5 # ลองเพิ่มเป็น 3 วินาที เพื่อทดสอบ

    def on_touch_down(self, touch):
        current_time = time.time()
        if current_time - self._last_touch_time < self.TOUCH_DEBOUNCE_TIME:
            print(f"Debounce: Touch ignored. Time diff: {current_time - self._last_touch_time:.3f}s")
            return True 
        print(touch)
        self._last_touch_time = current_time
        return super().on_touch_down(touch)


    def build(self):
        load_config() 
        Window.clearcolor = (1, 1, 1, 1) 

        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(AmountSelectionScreen(name='amount_selection'))
        sm.add_widget(PaymentScreen(name='payment'))
        sm.add_widget(ThankYouScreen(name='thank_you'))
        sm.add_widget(AdminAuthScreen(name='admin_auth'))
        sm.add_widget(AdminPanelScreen(name='admin_panel'))
        sm.add_widget(AddMoneyScreen(name='add_money_admin')) # <-- เพิ่มหน้านี้เข้ามา

        sm.current = 'welcome'
        return sm


if __name__ == '__main__':
    print("Main: GPIO module imported and initialized.")
    try:
        CoinMachineApp().run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user (Ctrl+C).")
    finally:
        #import os
        #os.system("sudo reboot") 
        print("Main: Application stopped. GPIO cleanup handled by coin_dispenser_gpio module.")
