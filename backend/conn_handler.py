import os
import time
import subprocess
from typing import Tuple, Optional

class ConnectionHandler:
    def __init__(self):
        self.device_id = None
        self.is_connected = False
        self.last_check = 0
        self.check_interval = 30  # Check connection every 30 seconds
    
    def check_adb_connection(self) -> bool:
        """Check if ADB device is connected"""
        try:
            current_time = time.time()
            
            # Only check if enough time has passed
            if current_time - self.last_check < self.check_interval and self.is_connected:
                return self.is_connected
            
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                devices = [line for line in lines[1:] if line.strip() and 'device' in line]
                
                if devices:
                    self.device_id = devices[0].split('\t')[0]
                    self.is_connected = True
                    self.last_check = current_time
                    print(f"✅ ADB device connected: {self.device_id}")
                    return True
                else:
                    self.is_connected = False
                    self.device_id = None
                    print("❌ No ADB devices found")
                    return False
            else:
                print(f"❌ ADB command failed: {result.stderr}")
                self.is_connected = False
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ ADB command timed out")
            self.is_connected = False
            return False
        except Exception as e:
            print(f"❌ ADB connection check error: {e}")
            self.is_connected = False
            return False
    
    def capture_screenshot(self, output_path: str) -> bool:
        """Capture screenshot from connected device"""
        try:
            if not self.check_adb_connection():
                return False
            
            # Capture screenshot
            result = subprocess.run(['adb', 'shell', 'screencap', '-p', '/sdcard/screen.png'],
                                  capture_output=True, timeout=15)
            
            if result.returncode != 0:
                print(f"❌ Screenshot capture failed: {result.stderr}")
                return False
            
            # Pull screenshot to local
            result = subprocess.run(['adb', 'pull', '/sdcard/screen.png', output_path],
                                  capture_output=True, timeout=15)
            
            if result.returncode == 0:
                print(f"✅ Screenshot saved to {output_path}")
                return True
            else:
                print(f"❌ Screenshot pull failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Screenshot capture timed out")
            return False
        except Exception as e:
            print(f"❌ Screenshot capture error: {e}")
            return False
    
    def tap_screen(self, x: int, y: int) -> bool:
        """Tap screen at specified coordinates"""
        try:
            if not self.check_adb_connection():
                return False
            
            result = subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)],
                                  capture_output=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ Tapped screen at ({x}, {y})")
                return True
            else:
                print(f"❌ Screen tap failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Screen tap timed out")
            return False
        except Exception as e:
            print(f"❌ Screen tap error: {e}")
            return False
    
    def swipe_screen(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """Swipe screen from (x1,y1) to (x2,y2)"""
        try:
            if not self.check_adb_connection():
                return False
            
            result = subprocess.run(['adb', 'shell', 'input', 'swipe', 
                                   str(x1), str(y1), str(x2), str(y2), str(duration)],
                                  capture_output=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ Swiped from ({x1},{y1}) to ({x2},{y2})")
                return True
            else:
                print(f"❌ Screen swipe failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Screen swipe timed out")
            return False
        except Exception as e:
            print(f"❌ Screen swipe error: {e}")
            return False
    
    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """Get device screen resolution"""
        try:
            if not self.check_adb_connection():
                return None
            
            result = subprocess.run(['adb', 'shell', 'wm', 'size'],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse output like "Physical size: 1080x2400"
                output = result.stdout.strip()
                if 'x' in output:
                    size_part = output.split(':')[-1].strip()
                    width, height = map(int, size_part.split('x'))
                    print(f"✅ Screen size: {width}x{height}")
                    return (width, height)
            
            print(f"❌ Failed to get screen size: {result.stderr}")
            return None
            
        except subprocess.TimeoutExpired:
            print("❌ Screen size query timed out")
            return None
        except Exception as e:
            print(f"❌ Screen size query error: {e}")
            return None
    
    def simulate_game_action(self, action: str, screen_size: Tuple[int, int] = None) -> bool:
        """Simulate game actions via ADB taps"""
        try:
            if not screen_size:
                screen_size = self.get_screen_size()
                if not screen_size:
                    return False
            
            width, height = screen_size
            
            # Define action coordinates (as percentages of screen size)
            action_coords = {
                'pick_from_deck': (0.8, 0.3),      # Top right area
                'pick_from_discard': (0.2, 0.3),   # Top left area  
                'drop_card': (0.5, 0.8),           # Bottom center
                'declare': (0.9, 0.9),             # Bottom right corner
                'sort_cards': (0.1, 0.9)           # Bottom left corner
            }
            
            if action.lower() in action_coords:
                x_percent, y_percent = action_coords[action.lower()]
                x = int(width * x_percent)
                y = int(height * y_percent)
                
                return self.tap_screen(x, y)
            else:
                print(f"❌ Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"❌ Game action simulation error: {e}")
            return False
    
    def get_connection_status(self) -> dict:
        """Get detailed connection status"""
        return {
            'is_connected': self.is_connected,
            'device_id': self.device_id,
            'last_check': self.last_check,
            'check_interval': self.check_interval
        }

