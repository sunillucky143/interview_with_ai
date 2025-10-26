#!/usr/bin/env python3
"""
HTTPS Server Runner for AI Proctoring System
This script helps run the proctoring system with HTTPS support for home network access.
"""

import os
import sys
import subprocess
import ssl
from pathlib import Path

def create_self_signed_cert():
    """Create a self-signed certificate for HTTPS"""
    try:
        import OpenSSL
        from OpenSSL import crypto
        
        # Create a key pair
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)
        
        # Create a self-signed certificate
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "State"
        cert.get_subject().L = "City"
        cert.get_subject().O = "AI Proctoring"
        cert.get_subject().OU = "IT Department"
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for 1 year
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')
        
        # Save certificate and key
        with open("cert.pem", "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open("key.pem", "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
            
        print("✅ Self-signed certificate created successfully!")
        return True
        
    except ImportError:
        print("❌ pyOpenSSL not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyOpenSSL"])
            print("✅ pyOpenSSL installed. Please run the script again.")
            return False
        except subprocess.CalledProcessError:
            print("❌ Failed to install pyOpenSSL. Please install manually: pip install pyOpenSSL")
            return False
    except Exception as e:
        print(f"❌ Error creating certificate: {e}")
        return False

def run_with_https():
    """Run the Flask app with HTTPS"""
    if not Path("cert.pem").exists() or not Path("key.pem").exists():
        print("🔐 Creating self-signed certificate...")
        if not create_self_signed_cert():
            return False
    
    print("🚀 Starting AI Proctoring System with HTTPS...")
    print("📱 Access the system at: https://localhost:5000")
    print("🌐 For home network access, use: https://YOUR_IP:5000")
    print("⚠️  Note: You may need to accept the self-signed certificate in your browser")
    print("🛑 Press Ctrl+C to stop the server")
    
    # Set environment variable for HTTPS
    os.environ['USE_HTTPS'] = 'true'
    
    # Import and run the app
    try:
        from app import app, socketio
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, 
                    ssl_context=('cert.pem', 'key.pem'))
    except Exception as e:
        print(f"❌ Error starting HTTPS server: {e}")
        return False
    
    return True

def get_local_ip():
    """Get the local IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def get_all_network_interfaces():
    """Get all available network interfaces"""
    import socket
    import subprocess
    import platform
    
    interfaces = []
    
    try:
        # Get hostname
        hostname = socket.gethostname()
        
        # Get all IP addresses
        for interface in socket.if_nameindex():
            try:
                # This is a simplified approach - in practice, you might want to use netifaces
                pass
            except:
                pass
        
        # Try to get IP using system commands
        system = platform.system().lower()
        if system == "windows":
            try:
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'IPv4' in line and '192.168.' in line:
                        ip = line.split(':')[-1].strip()
                        if ip and ip != '127.0.0.1':
                            interfaces.append(ip)
            except:
                pass
        else:  # Linux/Mac
            try:
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                ips = result.stdout.strip().split()
                for ip in ips:
                    if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                        interfaces.append(ip)
            except:
                pass
        
        # Fallback to socket method
        if not interfaces:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and ip != '127.0.0.1':
                interfaces.append(ip)
        
        return interfaces if interfaces else ["localhost"]
        
    except Exception as e:
        print(f"Warning: Could not detect network interfaces: {e}")
        return ["localhost"]

def check_port_availability(port=5000):
    """Check if port is available"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.close()
        return True
    except:
        return False

def check_firewall_windows():
    """Check Windows firewall status"""
    try:
        import subprocess
        result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles', 'state'], 
                              capture_output=True, text=True, shell=True)
        return 'ON' in result.stdout.upper()
    except:
        return False

def print_network_diagnostics():
    """Print network diagnostics and troubleshooting info"""
    print("\n🔍 Network Diagnostics:")
    print("-" * 30)
    
    # Check port availability
    if check_port_availability(5000):
        print("✅ Port 5000 is available")
    else:
        print("❌ Port 5000 is already in use")
        print("   Try closing other applications or use a different port")
    
    # Get all network interfaces
    interfaces = get_all_network_interfaces()
    print(f"📍 Detected IP addresses: {', '.join(interfaces)}")
    
    # Check Windows firewall
    import platform
    if platform.system().lower() == "windows":
        if check_firewall_windows():
            print("⚠️  Windows Firewall is ON - may block network access")
            print("   Solution: Add firewall rule for port 5000 or temporarily disable firewall")
        else:
            print("✅ Windows Firewall is OFF")
    
    print("\n🌐 Access URLs for other devices:")
    for ip in interfaces:
        if ip != "localhost":
            print(f"   - https://{ip}:5000")
    
    print("\n🔧 Troubleshooting Steps:")
    print("1. Make sure all devices are on the same WiFi network")
    print("2. Check Windows Firewall settings")
    print("3. Try accessing from the same computer first")
    print("4. Check if antivirus is blocking the connection")
    print("5. Try disabling Windows Defender temporarily")

def main():
    print("🎯 AI Proctoring System - Network Setup")
    print("=" * 50)
    
    # Run network diagnostics
    print_network_diagnostics()
    
    print("\n" + "=" * 50)
    choice = input("Choose an option:\n1. Run with HTTPS (for home network access)\n2. Run with HTTP (localhost only)\n3. Show detailed troubleshooting\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting with HTTPS for network access...")
        run_with_https()
    elif choice == "2":
        print("\n🚀 Starting with HTTP (localhost only)...")
        print("📱 Access the system at: http://localhost:5000")
        print("⚠️  Note: Camera access may be limited on home network with HTTP")
        print("🛑 Press Ctrl+C to stop the server")
        
        os.environ['USE_HTTPS'] = 'false'
        try:
            from app import app, socketio
            socketio.run(app, debug=True, host='0.0.0.0', port=5000)
        except Exception as e:
            print(f"❌ Error starting HTTP server: {e}")
    elif choice == "3":
        print_detailed_troubleshooting()
    else:
        print("❌ Invalid choice. Please run the script again and choose 1, 2, or 3.")

def print_detailed_troubleshooting():
    """Print detailed troubleshooting information"""
    print("\n🔧 Detailed Troubleshooting Guide")
    print("=" * 50)
    
    print("\n1. 🌐 Network Requirements:")
    print("   - All devices must be on the same WiFi network")
    print("   - Router should allow device-to-device communication")
    print("   - No guest network isolation enabled")
    
    print("\n2. 🔥 Windows Firewall Configuration:")
    print("   Option A - Add Firewall Rule:")
    print("   - Open Windows Defender Firewall")
    print("   - Click 'Advanced settings'")
    print("   - Click 'Inbound Rules' → 'New Rule'")
    print("   - Select 'Port' → 'TCP' → 'Specific local ports' → '5000'")
    print("   - Allow the connection")
    print("   ")
    print("   Option B - Temporarily Disable:")
    print("   - Open Windows Defender Firewall")
    print("   - Turn off firewall for private networks")
    print("   - (Remember to turn it back on later)")
    
    print("\n3. 🛡️ Antivirus Software:")
    print("   - Check if antivirus is blocking the connection")
    print("   - Add Python.exe to antivirus exceptions")
    print("   - Temporarily disable real-time protection for testing")
    
    print("\n4. 🔍 Testing Steps:")
    print("   Step 1: Test on same computer")
    print("   - Access https://localhost:5000")
    print("   - Verify camera works")
    print("   ")
    print("   Step 2: Test from another device")
    print("   - Use the IP address shown above")
    print("   - Accept the security certificate warning")
    print("   - Check browser console for errors")
    
    print("\n5. 🌍 Alternative Solutions:")
    print("   - Use ngrok for external access: ngrok http 5000")
    print("   - Use a different port: modify the script")
    print("   - Use a VPN to connect devices")
    
    print("\n6. 📱 Mobile Device Access:")
    print("   - Ensure mobile device is on same WiFi")
    print("   - Use Chrome or Safari browser")
    print("   - Allow camera permissions when prompted")
    
    input("\nPress Enter to continue...")
    main()  # Return to main menu

if __name__ == "__main__":
    main()
