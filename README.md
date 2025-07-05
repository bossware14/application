## Raspberry Pi5 + Module Relay 3 for Pi

   
  """
  sudo apt update
  
  sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
  
  sudo apt install pkg-config
  
  pip install kivy
  
  pip install requests

# เครื่องรับธนบัตร Genius 7 DIP
  Yellow: Inhibit
  
  PIN 1: Yellow (ไม่ใช้)
  
  PIN 2: Green (ไม่ใช้)
  
  PIN 3: Red ( ไฟ + 12V)
  
  PIN 4: Blue ( P6 - GPIO 23)
  
  PIN 5: Purple (GND)
  
  PIN 6: Orange (GND)
  
## เครืองจ่ายเหรียญ
  ""
  เซ็นเซอร์ Coin
  
  ขาว = GPIO 16
  
  แดง = 5V (Pi)
  
  ดำ = GND (Pi)

  มอเตอร์ ผ่าน Relay บน Raspberry Channel 1
