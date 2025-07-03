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
from kivy.uix.image import AsyncImage # สำหรับโหลดรูปภาพจาก URL
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock # สำหรับ Timer
from kivy.graphics import Color, Rectangle # สำหรับ Background
from kivy.core.window import Window # สำหรับ Fullscreen
from kivy.metrics import dp # สำหรับการปรับขนาดตาม DPI

import requests
import json
import threading
import time

# --- GPIO Control Module (จากโค้ดเดิมของคุณ) ---
# สมมติว่าโค้ด GPIO ของคุณถูกเก็บไว้ในไฟล์ชื่อ 'coin_dispenser_gpio.py'
# และมีฟังก์ชัน start_dispensing(num_coins) ที่เรียกใช้ได้
# รวมถึง Logic สำหรับ biller sensor และ coin sensor
import coin_dispenser_gpio as c_gpio 

# --- Global Configuration ---
API_KEY = "F8C04-06726831FD"
USERNAME = "coin_matchine_01"
BASE_PAYMENT_URL = "https://payment.all123th.com/api-pay"
CHECK_STATUS_BASE_URL = "https://api.all123th.com/payment-swiftpay/"
PAYMENT_TIMEOUT_SECONDS = 30 # เวลาที่หน้าชำระเงินจะหมดอายุ
COIN_PER_BAHT_RATIO = 10 # 1 เหรียญ = 10 บาท (ถ้าเหรียญบาทก็เปลี่ยนเป็น 1)

# --- Fullscreen Setup ---
Window.fullscreen = 'auto' # หรือ True

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
        # คุณสามารถเปลี่ยนรูปภาพเหล่านี้ได้
        self.ad_image = AsyncImage(source='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCfXf4DyE2leMSZJit9vtTQ8AKfGclP_npsAKwmJFoFXpd2SqZVD6QDEq0&s=10', 
                                    size_hint=(1, 0.7))
        layout.add_widget(self.ad_image)

        # ปุ่มเริ่มใช้งาน
        start_button = Button(text='แตะเพื่อเริ่ม', 
                              font_size=dp(40), 
                              size_hint=(1, 0.3),
                              background_color=(0.2, 0.7, 0.2, 1))
        start_button.bind(on_release=self.go_to_amount_selection)
        layout.add_widget(start_button)

        # ปุ่มสำหรับ Admin/ปิดแอป (อาจจะซ่อนหรือเล็กๆ อยู่มุมจอ)
        admin_button = Button(text='Admin', 
                              font_size=dp(20), 
                              size_hint=(1, 0.1), # ให้เล็กหน่อย
                              background_color=(0.5, 0.5, 0.5, 1))
        admin_button.bind(on_release=self.show_admin_popup)
        layout.add_widget(admin_button)


        self.add_widget(layout)
        
        # สามารถเพิ่ม Timer เพื่อเปลี่ยนรูปโฆษณาอัตโนมัติได้
        # Clock.schedule_interval(self.update_ad_image, 5) 

    def show_admin_popup(self, instance):
        # เรียกฟังก์ชันแสดง Popup รหัสผ่าน
        self.manager.get_screen('settings').show_password_popup(self.manager)

    def go_to_amount_selection(self, instance):
        self.manager.current = 'amount_selection'

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
        amounts = [20, 30, 50, 100]
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
        print(f"Selected amount: {amount} Baht")
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

        self.timer_label = Label(text=f'เวลาเหลือ: {PAYMENT_TIMEOUT_SECONDS} วินาที', font_size=dp(35), size_hint_y=0.1)
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
        self.timer_label.text = f'เวลาเหลือ: {PAYMENT_TIMEOUT_SECONDS} วินาที' # Reset timer text

    def on_enter(self):
        """
        เมื่อเข้าสู่หน้านี้ จะเริ่มกระบวนการสร้าง QR Code และ Timer
        """
        self.qr_image.source = 'https://image-charts.com/chart?chs=200x200&cht=qr&choe=UTF-8&chl=Generating+QR...' # Placeholder
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
        print("Payment process stopped.")

    def start_payment_process(self):
        """
        เริ่มต้นการสร้าง QR Code และ Timer
        """
        print(f"Requesting QR code for amount: {self.payment_amount}")
        self.payment_start_time = time.time()
        
        # เริ่ม Timer นับถอยหลัง
        if self.payment_timer:
            self.payment_timer.cancel() # ยกเลิก Timer เก่าถ้ามี
        self.payment_timer = Clock.schedule_interval(self.update_timer, 1)

        # เริ่มเธรดสร้าง QR Code
        threading.Thread(target=self._request_qr_code).start()

    def _request_qr_code(self):
        """
        เรียก API เพื่อสร้าง QR Code (ทำงานในเธรดแยก)
        """
        try:
            url = f"{BASE_PAYMENT_URL}?amount={self.payment_amount}&secretKey={API_KEY}&username={USERNAME}"
            print(f"Calling API: {url}")
            response = requests.get(url)
            response.raise_for_status() # ตรวจสอบ HTTP errors

            data = response.json()
            print(f"API Response: {json.dumps(data, indent=2)}")

            if data and data.get('status') == 'pedding':
                # ใช้ data.img หรือ data.url_check ตามที่คุณสะดวก
                qr_img_url = data.get('img')
                self.ref_id = data.get('refId')
                self.check_url = f"{CHECK_STATUS_BASE_URL}{self.ref_id}?type=json"

                if qr_img_url:
                    Clock.schedule_once(lambda dt: self.update_qr_image(qr_img_url))
                    # เริ่มตรวจสอบสถานะการชำระเงิน
                    if self.check_status_event:
                        self.check_status_event.cancel()
                    self.check_status_event = Clock.schedule_interval(self._check_payment_status, 3) # ตรวจสอบทุก 3 วินาที
                else:
                    print("Error: No QR image URL in response.")
                    Clock.schedule_once(lambda dt: self.show_error_popup("QR Code Error", "ไม่สามารถสร้าง QR Code ได้"))
            else:
                print(f"API response status not pedding: {data.get('status')}")
                Clock.schedule_once(lambda dt: self.show_error_popup("API Error", "การสร้าง QR Code ล้มเหลว"))

        except requests.exceptions.RequestException as e:
            print(f"Network or API error: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Network Error", f"ไม่สามารถเชื่อมต่อ API ได้: {e}"))
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Data Error", "รูปแบบข้อมูลจาก API ไม่ถูกต้อง"))
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            Clock.schedule_once(lambda dt: self.show_error_popup("Error", f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}"))

    def update_qr_image(self, img_url):
        self.qr_image.source = img_url
        self.qr_image.reload() # โหลดรูปภาพใหม่

    def update_timer(self, dt):
        """
        อัปเดต Timer นับถอยหลัง
        """
        time_elapsed = time.time() - self.payment_start_time
        time_remaining = max(0, PAYMENT_TIMEOUT_SECONDS - int(time_elapsed))
        self.timer_label.text = f'เวลาเหลือ: {time_remaining} วินาที'

        if time_remaining <= 0:
            self.payment_timer.cancel()
            if self.check_status_event:
                self.check_status_event.cancel()
            print("Payment time expired.")
            self.show_error_popup("หมดเวลา", "หมดเวลาชำระเงิน กรุณาลองใหม่อีกครั้ง")
            self.manager.current = 'amount_selection' # กลับไปหน้าเลือกจำนวนเงิน

    def _check_payment_status(self, dt):
        """
        ตรวจสอบสถานะการชำระเงินผ่าน API (ทำงานในเธรดแยก)
        """
        if not self.ref_id or not self.check_url:
            print("No refId or check_url to check status.")
            return

        threading.Thread(target=self.__check_payment_status_async).start()

    def __check_payment_status_async(self):
        """
        ฟังก์ชันหลักสำหรับตรวจสอบสถานะการชำระเงินแบบ Async
        """
        try:
            print(f"Checking payment status for {self.ref_id} at {self.check_url}")
            response = requests.get(self.check_url)
            response.raise_for_status()
            data = response.json()
            
            print(f"Check status response: {json.dumps(data, indent=2)}")

            if data and data.get('status') == 'success':
                # ชำระเงินสำเร็จ
                Clock.schedule_once(lambda dt: self.handle_payment_success(data.get('amount')))
            elif data and data.get('status') == 'cancel':
                # การชำระเงินถูกยกเลิก (จาก API หรือผู้ใช้)
                Clock.schedule_once(lambda dt: self.handle_payment_cancelled())
            # ถ้าเป็น 'pedding' ก็รอตรวจสอบต่อไป
            
        except requests.exceptions.RequestException as e:
            print(f"Network or API error during status check: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error during status check: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during status check: {e}")

    def handle_payment_success(self, paid_amount):
        """
        จัดการเมื่อชำระเงินสำเร็จ
        """
        print(f"Payment successful! Amount paid: {paid_amount}")
        # หยุด Timer และการตรวจสอบสถานะ
        if self.payment_timer:
            self.payment_timer.cancel()
        if self.check_status_event:
            self.check_status_event.cancel()
        
        # คำนวณจำนวนเหรียญที่จะจ่าย
        try:
            num_coins_to_dispense = int(float(paid_amount) * COIN_PER_BAHT_RATIO)
            print(f"Dispensing {num_coins_to_dispense} coins for {paid_amount} Baht.")
            # เรียกฟังก์ชันจ่ายเหรียญจาก c_gpio module
            c_gpio.start_dispensing(num_coins_to_dispense) 
            
            # ไปหน้าขอบคุณ
            self.manager.get_screen('thank_you').set_message(f'ชำระเงินสำเร็จ {paid_amount} บาท\nกำลังจ่ายเหรียญ {num_coins_to_dispense} เหรียญ')
            self.manager.current = 'thank_you'

        except ValueError:
            print(f"Error converting paid_amount '{paid_amount}' to float.")
            self.show_error_popup("Error", "ไม่สามารถประมวลผลจำนวนเงินที่จ่ายได้")
            self.manager.current = 'amount_selection' # หรือกลับไปหน้าเลือกเงิน
        

    def handle_payment_cancelled(self):
        """
        จัดการเมื่อการชำระเงินถูกยกเลิก
        """
        print("Payment cancelled by API.")
        self.show_error_popup("การชำระเงินถูกยกเลิก", "การชำระเงินถูกยกเลิก กรุณาลองใหม่อีกครั้ง")
        self.manager.current = 'amount_selection' # กลับไปหน้าเลือกจำนวนเงิน

    def cancel_payment(self, instance):
        """
        ผู้ใช้กดปุ่มยกเลิกการชำระเงิน
        """
        print("User cancelled payment.")
        self.manager.current = 'amount_selection'

    def show_error_popup(self, title, message):
        """
        แสดง Popup ข้อความแจ้งเตือน
        """
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(25)))
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
        self.message_label = Label(text='ขอบคุณ!', font_size=dp(60))
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
    หน้าจอตั้งค่า ที่มีระบบรหัสผ่าน
    """
    # รหัสผ่านสำหรับ Admin
    ADMIN_PASSWORD = "123456" # *** ควรเก็บรหัสผ่านในไฟล์ config ไม่ใช่ hardcode ***

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self.password_popup = None # สำหรับเก็บ reference ของ popup รหัสผ่าน

        # UI สำหรับหน้าตั้งค่าหลัก (จะแสดงเมื่อใส่รหัสผ่านถูกต้อง)
        self.settings_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        self.settings_layout.add_widget(Label(text='หน้าจอตั้งค่า', font_size=dp(40), size_hint_y=0.2))

        # ปุ่มปิดแอปพลิเคชัน
        shutdown_app_button = Button(text='ปิดแอปพลิเคชัน', 
                                     font_size=dp(35), 
                                     background_color=(0.8, 0.2, 0.2, 1))
        shutdown_app_button.bind(on_release=self.shutdown_application)
        self.settings_layout.add_widget(shutdown_app_button)

        # ตัวอย่าง Input สำหรับตั้งค่า API (เอามาจากโค้ดเดิม)
        self.settings_layout.add_widget(Label(text='API Key:', font_size=dp(25)))
        self.api_key_input = TextInput(text=API_KEY, multiline=False, font_size=dp(25))
        self.settings_layout.add_widget(self.api_key_input)

        self.settings_layout.add_widget(Label(text='Username:', font_size=dp(25)))
        self.username_input = TextInput(text=USERNAME, multiline=False, font_size=dp(25))
        self.settings_layout.add_widget(self.username_input)

        save_button = Button(text='บันทึกการตั้งค่า', font_size=dp(30), background_color=(0.2, 0.7, 0.2, 1))
        save_button.bind(on_release=self.save_settings)
        self.settings_layout.add_widget(save_button)

        back_button = Button(text='ย้อนกลับ', font_size=dp(30), background_color=(0.8, 0.4, 0.2, 1))
        back_button.bind(on_release=self.go_back_to_welcome)
        self.settings_layout.add_widget(back_button)

        # หน้าจอนี้จะยังไม่แสดง layout นี้จนกว่าจะใส่รหัสผ่านถูกต้อง
        # เราจะ add_widget(self.settings_layout) ใน on_enter_admin_mode

        self.add_widget(self.settings_layout) # เพิ่มไว้ก่อน แต่จะ set opacity/disabled
        self.settings_layout.opacity = 0 # ซ่อนไว้ก่อน
        self.settings_layout.disabled = True # ปิดการใช้งาน

    def show_password_popup(self, manager_instance):
        """
        แสดง Popup สำหรับใส่รหัสผ่าน
        """
        self.manager_instance = manager_instance # เก็บ reference ของ ScreenManager

        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text='ป้อนรหัสผ่าน Admin:', font_size=dp(30)))
        self.password_input = TextInput(password=True, multiline=False, font_size=dp(30))
        popup_layout.add_widget(self.password_input)

        button_layout = BoxLayout(size_hint_y=0.3, spacing=dp(10))
        ok_button = Button(text='ตกลง', font_size=dp(25))
        ok_button.bind(on_release=self.check_password)
        button_layout.add_widget(ok_button)

        cancel_button = Button(text='ยกเลิก', font_size=dp(25))
        cancel_button.bind(on_release=lambda x: self.password_popup.dismiss())
        button_layout.add_widget(cancel_button)

        popup_layout.add_widget(button_layout)

        self.password_popup = Popup(title='Admin Access', 
                                    content=popup_layout, 
                                    size_hint=(0.8, 0.5), 
                                    auto_dismiss=False)
        self.password_popup.open()
        self.manager.current = 'settings' # สลับมาหน้า settings

    def check_password(self, instance):
        """
        ตรวจสอบรหัสผ่านที่ผู้ใช้ป้อน
        """
        if self.password_input.text == self.ADMIN_PASSWORD:
            self.password_popup.dismiss()
            self.on_enter_admin_mode() # เรียกฟังก์ชันเมื่อเข้าสู่โหมด Admin
        else:
            self.show_error_popup("รหัสผ่านผิด", "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
            self.password_input.text = '' # ล้างช่องใส่รหัสผ่าน

    def on_enter_admin_mode(self):
        """
        เมื่อเข้าสู่โหมด Admin สำเร็จ
        """
        print("Admin mode entered successfully.")
        self.settings_layout.opacity = 1 # ทำให้ UI ตั้งค่าปรากฏ
        self.settings_layout.disabled = False # เปิดการใช้งาน UI

    def on_leave(self):
        """
        เมื่อออกจากหน้า Settings ให้กลับไปซ่อน UI ของ Admin
        """
        self.settings_layout.opacity = 0
        self.settings_layout.disabled = True
        self.password_input.text = '' # ล้างรหัสผ่านเมื่อออก

    def shutdown_application(self, instance):
        """
        ฟังก์ชันปิดแอปพลิเคชัน
        """
        print("Shutting down application...")
        App.get_running_app().stop() # สั่งให้ Kivy App หยุดทำงาน
        # หากต้องการปิด Raspberry Pi ด้วย (ไม่ใช่แค่แอป)
        # import os
        # os.system("sudo shutdown -h now") # ต้องให้สิทธิ์ NOPASSWD ใน sudoers สำหรับผู้ใช้


    def save_settings(self, instance):
        # TODO: Implement actual save logic (e.g., to a config file)
        global API_KEY, USERNAME
        API_KEY = self.api_key_input.text
        USERNAME = self.username_input.text
        print("Settings saved (in-memory only for now).")
        self.show_error_popup("บันทึกการตั้งค่า", "บันทึกข้อมูลเรียบร้อย")

    def go_back_to_welcome(self, instance):
        self.manager.current = 'welcome'

    def show_error_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        popup_layout.add_widget(Label(text=message, font_size=dp(25)))
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
    คลาสหลักของแอปพลิเคชัน
    """
    def build(self):
        # ตั้งค่า Background สีดำ
        Window.clearcolor = (0, 0, 0, 1) 

        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(AmountSelectionScreen(name='amount_selection'))
        sm.add_widget(PaymentScreen(name='payment'))
        sm.add_widget(ThankYouScreen(name='thank_you'))
        sm.add_widget(SettingsScreen(name='settings')) # หน้าตั้งค่า

        # กำหนดหน้าเริ่มต้น
        sm.current = 'welcome'
        return sm

if __name__ == '__main__':
    # Initialise GPIO (should be done once at the start of the program)
    # Ensure this is called only once and handles cleanup in finally block
    try:
        # Initialise the GPIO module from coin_dispenser_gpio
        # You might need to call an init function if it's not done in the global scope of that file
        # c_gpio.setup_gpio_pins() # สมมติว่ามีฟังก์ชันนี้ใน coin_dispenser_gpio.py
        # Or just ensure the global setup in coin_dispenser_gpio.py is executed when imported
        print("GPIO module imported and initialized.")
        CoinMachineApp().run()
    except KeyboardInterrupt:
        print("Application interrupted.")
    finally:
        # This cleanup will be handled by the coin_dispenser_gpio module's own finally block
        # when the main script exits, but you can explicitly call it here if needed.
        # c_gpio.cleanup_gpio() # สมมติว่ามีฟังก์ชันนี้ใน coin_dispenser_gpio.py
        print("Application stopped. GPIO cleanup handled by coin_dispenser_gpio module.")

