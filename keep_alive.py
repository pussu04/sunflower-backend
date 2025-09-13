#!/usr/bin/env python3
"""
Keep-Alive System for DualScan.ai Backend
Prevents server from going to sleep by making periodic requests
"""

import requests
import time
import threading
import os
from datetime import datetime

class KeepAliveService:
    def __init__(self, server_url=None, interval=300):  # 5 minutes default
        self.server_url = server_url or os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:5000')
        self.interval = interval  # seconds between pings
        self.running = False
        self.thread = None
        
    def ping_server(self):
        """Send a ping to keep the server alive"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=30)
            if response.status_code == 200:
                print(f"🟢 Keep-alive ping successful at {datetime.now().strftime('%H:%M:%S')}")
                return True
            elif response.status_code == 502:
                print(f"🟡 Server starting up (502) at {datetime.now().strftime('%H:%M:%S')} - attempting warmup")
                # Try to warm up the server
                try:
                    warmup_response = requests.get(f"{self.server_url}/warmup", timeout=60)
                    if warmup_response.status_code == 200:
                        print(f"🔥 Server warmup successful")
                        return True
                    else:
                        print(f"🟡 Warmup returned {warmup_response.status_code}")
                        return False
                except Exception as warmup_error:
                    print(f"🟡 Warmup failed: {str(warmup_error)}")
                    return False
            elif response.status_code == 503:
                print(f"🟡 Server temporarily unavailable (503) at {datetime.now().strftime('%H:%M:%S')}")
                return False
            else:
                print(f"🟡 Keep-alive ping returned {response.status_code} at {datetime.now().strftime('%H:%M:%S')}")
                return False
        except requests.exceptions.Timeout:
            print(f"🟡 Keep-alive ping timed out at {datetime.now().strftime('%H:%M:%S')} - server may be sleeping")
            return False
        except requests.exceptions.ConnectionError:
            print(f"🟡 Connection error at {datetime.now().strftime('%H:%M:%S')} - server may be starting up")
            return False
        except Exception as e:
            print(f"🔴 Keep-alive ping failed at {datetime.now().strftime('%H:%M:%S')}: {str(e)}")
            return False
    
    def keep_alive_loop(self):
        """Main keep-alive loop"""
        print(f"🚀 Keep-alive service started for {self.server_url}")
        print(f"⏰ Pinging every {self.interval} seconds")
        
        while self.running:
            try:
                self.ping_server()
                time.sleep(self.interval)
            except KeyboardInterrupt:
                print("🛑 Keep-alive service stopped by user")
                break
            except Exception as e:
                print(f"❌ Keep-alive loop error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def start(self):
        """Start the keep-alive service"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.keep_alive_loop, daemon=True)
            self.thread.start()
            print("✅ Keep-alive service started")
    
    def stop(self):
        """Stop the keep-alive service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Keep-alive service stopped")

# Global keep-alive instance
keep_alive_service = None

def start_keep_alive(server_url=None, interval=300):
    """Start the keep-alive service"""
    global keep_alive_service
    if keep_alive_service is None:
        keep_alive_service = KeepAliveService(server_url, interval)
        keep_alive_service.start()
    return keep_alive_service

def stop_keep_alive():
    """Stop the keep-alive service"""
    global keep_alive_service
    if keep_alive_service:
        keep_alive_service.stop()
        keep_alive_service = None

if __name__ == "__main__":
    # Run as standalone script
    import sys
    
    server_url = sys.argv[1] if len(sys.argv) > 1 else None
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    service = KeepAliveService(server_url, interval)
    
    try:
        service.start()
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down keep-alive service...")
        service.stop()