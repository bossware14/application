import RPi.GPIO as GPIO
import time

class TM1637:
    """
    Driver for the TM1637 4-digit 7-segment display.
    Adapted from micropython-tm1637 by mcauser
    """
    DIO_PIN = None
    CLK_PIN = None

    def __init__(self, clk_pin, dio_pin, brightness=7):
        self.CLK_PIN = clk_pin
        self.DIO_PIN = dio_pin
        self.brightness = min(brightness, 7) # 0-7

        GPIO.setmode(GPIO.BCM) # Use BCM numbering for GPIO pins
        GPIO.setup(self.CLK_PIN, GPIO.OUT)
        GPIO.setup(self.DIO_PIN, GPIO.OUT)

        self._point = 0x00 # Colon state
        self.clear()
        self.set_brightness(self.brightness)

    def _start(self):
        GPIO.output(self.DIO_PIN, GPIO.HIGH)
        GPIO.output(self.CLK_PIN, GPIO.HIGH)
        GPIO.output(self.DIO_PIN, GPIO.LOW)

    def _stop(self):
        GPIO.output(self.CLK_PIN, GPIO.LOW)
        GPIO.output(self.DIO_PIN, GPIO.LOW)
        GPIO.output(self.CLK_PIN, GPIO.HIGH)
        GPIO.output(self.DIO_PIN, GPIO.HIGH)

    def _write_byte(self, data):
        for i in range(8):
            GPIO.output(self.CLK_PIN, GPIO.LOW)
            if data & 0x01:
                GPIO.output(self.DIO_PIN, GPIO.HIGH)
            else:
                GPIO.output(self.DIO_PIN, GPIO.LOW)
            data >>= 1
            GPIO.output(self.CLK_PIN, GPIO.HIGH)
        # Wait for ACK
        GPIO.output(self.CLK_PIN, GPIO.LOW)
        GPIO.setup(self.DIO_PIN, GPIO.IN) # Set DIO to input for ACK
        while GPIO.input(self.DIO_PIN): # Wait for DIO to go low (ACK)
            pass # Or add a timeout for robustness
        GPIO.setup(self.DIO_PIN, GPIO.OUT) # Set DIO back to output
        GPIO.output(self.CLK_PIN, GPIO.HIGH)

    def set_brightness(self, brightness):
        """Set the brightness of the display (0-7)."""
        self.brightness = min(brightness, 7)
        self._write_command(0x88 + self.brightness)

    def _write_command(self, cmd):
        self._start()
        self._write_byte(cmd)
        self._stop()

    def _display_data(self, data):
        self._write_command(0x40) # Data command
        self._start()
        self._write_byte(0xC0) # Address command (start from 0)
        for digit_data in data:
            self._write_byte(digit_data)
        self._stop()
        self._write_command(0x88 + self.brightness) # Display control

    def write(self, segments, colon=False):
        """
        Write raw segments to the display.
        segments is a list of 4 bytes, one for each digit.
        Each byte represents the segments to light up (0x01 for A, 0x02 for B, etc.)
        """
        self._point = 0x02 if colon else 0x00 # Update colon state
        display_segments = list(segments)
        if colon:
            display_segments[1] |= 0x80 # Set DP for colon (usually 2nd digit)
        self._display_data(display_segments)

    def show(self, string, colon=False):
        """
        Display a string of up to 4 digits.
        Only digits 0-9 and '-' are supported.
        """
        segments = []
        for char in string.ljust(4)[:4]: # Pad with spaces and limit to 4 chars
            if char == '0': segments.append(0x3F)
            elif char == '1': segments.append(0x06)
            elif char == '2': segments.append(0x5B)
            elif char == '3': segments.append(0x4F)
            elif char == '4': segments.append(0x66)
            elif char == '5': segments.append(0x6D)
            elif char == '6': segments.append(0x7D)
            elif char == '7': segments.append(0x07)
            elif char == '8': segments.append(0x7F)
            elif char == '9': segments.append(0x6F)
            elif char == '-': segments.append(0x40)
            elif char == ' ': segments.append(0x00)
            else: segments.append(0x00) # Unknown char as blank
        self.write(segments, colon)

    def show_number(self, num, colon=False):
        """Display an integer number (up to 4 digits)."""
        if isinstance(num, int) and -999 <= num <= 9999:
            s = str(num).zfill(4)
            self.show(s, colon)
        else:
            self.show("----") # Indicate error or out of range

    def clear(self):
        """Clear the display."""
        self.write([0, 0, 0, 0])

    def cleanup(self):
        GPIO.cleanup() # Clean up GPIO settings when done
