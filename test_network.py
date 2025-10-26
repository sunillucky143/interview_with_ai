#!/usr/bin/env python3
"""
Network Connectivity Test for AI Proctoring System
This script tests network connectivity and helps diagnose issues.
"""

import socket
import subprocess
import platform
import requests
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Network Test Successful!</h1><p>Connection working from other device.</p>')

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def test_port_listening(ip, port):
    """Test if port is listening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def start_test_server(port=5001):
    """Start a simple test server"""
    try:
        server = HTTPServer(('0.0.0.0', port), TestHandler)
        print(f"✅ Test server started on port {port}")
        print(f"   Test URL: http://{get_local_ip()}:{port}")
        print("   Press Ctrl+C to stop")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Failed to start test server: {e}")

def test_connectivity():
    """Test basic network connectivity"""
    print("🔍 Testing Network Connectivity...")
    print("-" * 40)
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"📍 Local IP: {local_ip}")
    
    # Test if we can bind to port 5000
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 5000))
        sock.close()
        print("✅ Port 5000 is available")
    except Exception as e:
        print(f"❌ Port 5000 is not available: {e}")
        return False
    
    # Test if we can bind to all interfaces
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', 5001))
        sock.close()
        print("✅ Can bind to all interfaces (0.0.0.0)")
    except Exception as e:
        print(f"❌ Cannot bind to all interfaces: {e}")
        print("   This may prevent other devices from connecting")
    
    # Test localhost connectivity
    if test_port_listening('localhost', 5000):
        print("✅ Port 5000 is listening on localhost")
    else:
        print("ℹ️  Port 5000 is not currently listening (server not running)")
    
    return True

def check_firewall_status():
    """Check Windows firewall status"""
    if platform.system().lower() != "windows":
        return
    
    print("\n🔥 Checking Windows Firewall...")
    print("-" * 40)
    
    try:
        result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles', 'state'], 
                              capture_output=True, text=True, shell=True)
        if 'ON' in result.stdout.upper():
            print("⚠️  Windows Firewall is ON")
            print("   This may block connections from other devices")
            print("   Run 'python configure_firewall.py' to add rules")
        else:
            print("✅ Windows Firewall is OFF")
    except Exception as e:
        print(f"❌ Could not check firewall status: {e}")

def test_from_other_device():
    """Instructions for testing from other device"""
    print("\n📱 Testing from Other Device...")
    print("-" * 40)
    
    local_ip = get_local_ip()
    print("1. Start the test server:")
    print(f"   python test_network.py --server")
    print()
    print("2. From another device on the same network:")
    print(f"   Open browser and go to: http://{local_ip}:5001")
    print()
    print("3. If you see 'Network Test Successful!', connectivity is working")
    print("4. If not, check firewall settings and network configuration")

def main():
    print("🌐 Network Connectivity Test for AI Proctoring System")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        start_test_server()
        return
    
    # Run connectivity tests
    if not test_connectivity():
        print("\n❌ Basic connectivity test failed")
        return
    
    # Check firewall
    check_firewall_status()
    
    # Show testing instructions
    test_from_other_device()
    
    print("\n🎯 Next Steps:")
    print("1. Run 'python configure_firewall.py' as Administrator")
    print("2. Run 'python test_network.py --server' to test connectivity")
    print("3. Test from another device using the provided URL")
    print("4. If successful, run 'python run_https.py' to start the proctoring system")
    
    print("\n📋 Troubleshooting Checklist:")
    print("□ All devices on same WiFi network")
    print("□ Windows Firewall configured")
    print("□ No antivirus blocking connections")
    print("□ Router allows device-to-device communication")
    print("□ Using correct IP address (not localhost)")

if __name__ == "__main__":
    import sys
    main()
