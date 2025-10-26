#!/usr/bin/env python3
"""
Windows Firewall Configuration Script for AI Proctoring System
This script helps configure Windows Firewall to allow network access.
"""

import subprocess
import sys
import os

def run_as_admin():
    """Check if running as administrator"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_firewall_rule():
    """Add Windows Firewall rule for port 5000"""
    try:
        # Add inbound rule
        cmd_inbound = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=AI Proctoring System (Inbound)',
            'dir=in',
            'action=allow',
            'protocol=TCP',
            'localport=5000'
        ]
        
        result_inbound = subprocess.run(cmd_inbound, capture_output=True, text=True, shell=True)
        
        # Add outbound rule
        cmd_outbound = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=AI Proctoring System (Outbound)',
            'dir=out',
            'action=allow',
            'protocol=TCP',
            'localport=5000'
        ]
        
        result_outbound = subprocess.run(cmd_outbound, capture_output=True, text=True, shell=True)
        
        if result_inbound.returncode == 0 and result_outbound.returncode == 0:
            print("✅ Firewall rules added successfully!")
            return True
        else:
            print("❌ Failed to add firewall rules")
            print(f"Inbound error: {result_inbound.stderr}")
            print(f"Outbound error: {result_outbound.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding firewall rules: {e}")
        return False

def remove_firewall_rule():
    """Remove Windows Firewall rules for port 5000"""
    try:
        # Remove inbound rule
        cmd_inbound = [
            'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
            'name=AI Proctoring System (Inbound)'
        ]
        
        # Remove outbound rule
        cmd_outbound = [
            'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
            'name=AI Proctoring System (Outbound)'
        ]
        
        subprocess.run(cmd_inbound, capture_output=True, text=True, shell=True)
        subprocess.run(cmd_outbound, capture_output=True, text=True, shell=True)
        
        print("✅ Firewall rules removed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error removing firewall rules: {e}")
        return False

def check_firewall_rules():
    """Check if firewall rules exist"""
    try:
        cmd = ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=AI Proctoring System (Inbound)']
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return "AI Proctoring System (Inbound)" in result.stdout
    except:
        return False

def main():
    print("🔥 Windows Firewall Configuration for AI Proctoring System")
    print("=" * 60)
    
    # Check if running as administrator
    if not run_as_admin():
        print("⚠️  This script needs to run as Administrator!")
        print("   Right-click on Command Prompt or PowerShell")
        print("   Select 'Run as administrator'")
        print("   Then run: python configure_firewall.py")
        input("\nPress Enter to exit...")
        return
    
    print("✅ Running as Administrator")
    
    # Check current rules
    if check_firewall_rules():
        print("✅ Firewall rules already exist")
        choice = input("Do you want to remove the existing rules? (y/n): ").strip().lower()
        if choice == 'y':
            remove_firewall_rule()
    else:
        print("ℹ️  No existing firewall rules found")
        choice = input("Do you want to add firewall rules for port 5000? (y/n): ").strip().lower()
        if choice == 'y':
            if add_firewall_rule():
                print("\n🎉 Firewall configuration complete!")
                print("   You can now access the proctoring system from other devices")
                print("   Run 'python run_https.py' to start the server")
            else:
                print("\n❌ Failed to configure firewall")
                print("   You may need to manually add firewall rules")
        else:
            print("ℹ️  Skipping firewall configuration")
    
    print("\n📋 Manual Firewall Configuration (if needed):")
    print("1. Open Windows Defender Firewall")
    print("2. Click 'Advanced settings'")
    print("3. Click 'Inbound Rules' → 'New Rule'")
    print("4. Select 'Port' → 'TCP' → 'Specific local ports' → '5000'")
    print("5. Allow the connection")
    print("6. Repeat for 'Outbound Rules'")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
