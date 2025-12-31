#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import subprocess
import requests
import json
import argparse
import pickle
import threading
import schedule
from datetime import datetime
from pathlib import Path

# Configuration file paths
CONFIG_DIR = Path.home() / ".tor_manager"
CONFIG_FILE = CONFIG_DIR / "config.pkl"
INSTANCES_FILE = CONFIG_DIR / "instances.pkl"

# Create config directory if not exists
CONFIG_DIR.mkdir(exist_ok=True)

class TorInstance:
    def __init__(self, name, country, port, base_dir=None):
        self.name = name
        self.country = country.upper()
        self.port = port
        # Create instance-specific directory
        if base_dir:
            self.base_dir = Path(base_dir)
            self.data_dir = str(self.base_dir / name)
        else:
            self.data_dir = f"/root/tor/{name}"
        self.torrc = f"{self.data_dir}/torrc.conf"
        self.ip = None
        self.city = None
        self.ping = None
        self.speed = None
        self.bridge_type = None
        self.bridge_count = 0
        # Store best results from multiple attempts
        self.best_results = []
        
    def to_dict(self):
        return {
            'name': self.name,
            'country': self.country,
            'port': self.port,
            'data_dir': self.data_dir,
            'torrc': self.torrc
        }

class TorManager:
    def __init__(self):
        self.instances = {}
        self.bridge_data = None
        self.max_country_retries = 5
        self.test_schedule = None
        self.attempts_per_country = 3  # Test 3 times for each country
        self.load_config()
        
    def save_config(self):
        """Save current configuration"""
        config = {
            'instances': {name: inst.to_dict() for name, inst in self.instances.items()},
            'bridge_data': self.bridge_data,
            'test_schedule': self.test_schedule,
            'attempts_per_country': self.attempts_per_country
        }
        with open(CONFIG_FILE, 'wb') as f:
            pickle.dump(config, f)
        print("[+] Configuration saved")
        
    def load_config(self):
        """Load saved configuration"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'rb') as f:
                    config = pickle.load(f)
                    for name, inst_dict in config.get('instances', {}).items():
                        self.instances[name] = TorInstance(
                            inst_dict['name'],
                            inst_dict['country'],
                            inst_dict['port'],
                            str(Path(inst_dict['data_dir']).parent)
                        )
                    self.bridge_data = config.get('bridge_data')
                    self.test_schedule = config.get('test_schedule')
                    self.attempts_per_country = config.get('attempts_per_country', 3)
                print(f"[+] Loaded {len(self.instances)} saved instances")
            except Exception as e:
                print(f"[!] Error loading config: {e}")
                
    def add_instance_interactive(self):
        """Add new Tor instance interactively"""
        print("\n" + "="*50)
        print("ADD NEW TOR INSTANCE")
        print("="*50)
        
        # Ask for base directory once
        base_dir = input("Base directory for Tor instances [/root/tor]: ").strip()
        if not base_dir:
            base_dir = "/root/tor"
        
        # Create base directory if not exists
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        
        while True:
            name = input("\nInstance name (e.g., tor1) [or 'done' to finish]: ").strip()
            if name.lower() == 'done':
                break
                
            if name in self.instances:
                print(f"[!] Instance '{name}' already exists!")
                continue
                
            country = input("Country code (e.g., US, GB, FR): ").strip().upper()
            if len(country) != 2:
                print("[!] Country code must be 2 letters!")
                continue
                
            while True:
                try:
                    port = int(input(f"SOCKS port (e.g., 9050): ").strip())
                    # Check if port already in use
                    if any(inst.port == port for inst in self.instances.values()):
                        print(f"[!] Port {port} already in use!")
                        continue
                    break
                except ValueError:
                    print("[!] Invalid port number!")
                    
            # Create instance with base directory
            inst = TorInstance(name, country, port, base_dir)
            
            # Create instance directory
            Path(inst.data_dir).mkdir(parents=True, exist_ok=True)
            
            self.instances[name] = inst
            print(f"[+] Added instance: {name} ({country}) on port {port}")
            print(f"    Data directory: {inst.data_dir}")
            
        self.save_config()
        
    def get_ip_and_location(self, port):
        """Get IP and check geographic location - using all services from original code"""
        proxies = {"http": f"socks5://127.0.0.1:{port}", "https": f"socks5://127.0.0.1:{port}"}
        
        # All IP services from original code
        ip_services = [
            "http://api.ipify.org",
            "http://checkip.amazonaws.com",
            "http://icanhazip.com",
            "http://ipecho.net/plain",
            "http://myexternalip.com/raw"
        ]
        
        # All location services from original code
        location_services = [
            {
                'url': 'http://ip-api.com/json/{ip}',
                'country_key': 'countryCode',
                'city_key': 'city'
            },
            {
                'url': 'https://ipapi.co/{ip}/json/',
                'country_key': 'country_code',
                'city_key': 'city'
            },
            {
                'url': 'http://ipwho.is/{ip}',
                'country_key': 'country_code',
                'city_key': 'city'
            },
            {
                'url': 'http://www.geoplugin.net/json.gp?ip={ip}',
                'country_key': 'geoplugin_countryCode',
                'city_key': 'geoplugin_city'
            }
        ]
        
        ip = None
        ping_time = 9999
        
        # Try to get IP
        for service in ip_services:
            try:
                start_time = time.time()
                r = requests.get(service, proxies=proxies, timeout=15)
                ping_time = int((time.time() - start_time) * 1000)
                ip = r.text.strip()
                if ip and len(ip.split('.')) == 4:
                    break
            except:
                continue
                
        if not ip:
            return None, "Error", "No IP", 9999
            
        # Try to get location
        for service in location_services:
            try:
                url = service['url'].format(ip=ip)
                location_r = requests.get(url, timeout=10)
                
                if location_r.status_code == 200:
                    location_data = location_r.json()
                    country = location_data.get(service['country_key'], '').upper()
                    city = location_data.get(service['city_key'], 'Unknown')
                    
                    if country and len(country) == 2:
                        return ip, country, city, ping_time
            except:
                continue
                
        return ip, "Unknown", "Unknown", ping_time
        
    def test_speed(self, port):
        """Test actual bandwidth through Tor - using all methods from original code"""
        proxies = {"http": f"socks5://127.0.0.1:{port}"}
        
        # Test URLs from original code
        test_data = [
            ("http://httpbin.org/bytes/50000", 50000),  # 50KB
            ("http://httpbin.org/bytes/25000", 25000),  # 25KB  
            ("http://speedtest.ftp.otenet.gr/files/test100k.db", 100000),  # 100KB
        ]
        
        for test_url, expected_size in test_data:
            try:
                print(f"      Testing speed with {expected_size//1000}KB download...")
                start_time = time.time()
                
                response = requests.get(test_url, proxies=proxies, timeout=12)
                
                if response.status_code == 200:
                    download_time = time.time() - start_time
                    actual_size = len(response.content)
                    
                    if download_time > 0 and actual_size > 1000:  # At least 1KB
                        # Calculate Mbps
                        bits_downloaded = actual_size * 8
                        mbps = bits_downloaded / (download_time * 1000000)
                        
                        print(f"      Downloaded {actual_size} bytes in {download_time:.2f}s = {mbps:.2f} Mbps")
                        return round(mbps, 2)
                        
            except Exception as e:
                print(f"      Failed: {str(e)[:30]}...")
                continue
        
        # Fallback: ping-based speed estimation from original code
        try:
            ping_times = []
            for i in range(3):
                start_time = time.time()
                response = requests.get("http://httpbin.org/status/200", proxies=proxies, timeout=8)
                if response.status_code == 200:
                    ping_time = (time.time() - start_time) * 1000
                    ping_times.append(ping_time)
            
            if ping_times:
                avg_ping = sum(ping_times) / len(ping_times)
                # Estimate speed based on ping (very rough approximation)
                estimated_mbps = max(0.1, 10 / (avg_ping / 100))
                print(f"      Fallback: Avg ping {avg_ping:.0f}ms ≈ {estimated_mbps:.1f} Mbps estimate")
                return round(estimated_mbps, 1)
        except:
            pass
        
        print("      Speed test failed")
        return 0
        
    def detect_bridge_type(self, bridge_line):
        """Detect bridge type from bridge line"""
        if not bridge_line:
            return None
        
        bridge_lower = bridge_line.lower()
        if 'obfs4' in bridge_lower:
            return 'obfs4'
        elif 'snowflake' in bridge_lower:
            return 'snowflake'
        elif 'meek-azure' in bridge_lower or 'meek_lite' in bridge_lower:
            return 'meek-azure'
        elif 'webtunnel' in bridge_lower:
            return 'webtunnel'
        else:
            return 'unknown'
            
    def parse_bridge_input(self, bridge_input):
        """Parse multiple bridge lines and detect types"""
        if not bridge_input.strip():
            return None, None
        
        lines = [line.strip() for line in bridge_input.strip().split('\n') if line.strip()]
        
        bridge_lines = []
        bridge_types = set()
        
        for line in lines:
            if not line.startswith("Bridge"):
                line = f"Bridge {line}"
            
            bridge_lines.append(line)
            bridge_type = self.detect_bridge_type(line)
            if bridge_type:
                bridge_types.add(bridge_type)
        
        if len(bridge_types) == 1:
            return bridge_lines, list(bridge_types)[0]
        elif len(bridge_types) > 1:
            print(f"[!] Mixed bridge types detected: {', '.join(bridge_types)}")
            return bridge_lines, list(bridge_types)[0]
        else:
            return bridge_lines, 'unknown'
            
    def create_torrc(self, inst, use_bridges=False):
        """Create torrc configuration file with all settings from original code"""
        import random
        circuit_period = random.randint(15, 45)
        
        # Ensure directory exists
        Path(inst.data_dir).mkdir(parents=True, exist_ok=True)
        
        config = f"""SocksPort {inst.port}
DataDirectory {inst.data_dir}
"""
        
        if use_bridges and self.bridge_data:
            bridge_lines, bridge_type = self.bridge_data
            config += "UseBridges 1\n"
            
            # Add transport plugins based on bridge type
            if bridge_type == 'obfs4':
                config += "ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n"
            elif bridge_type == 'snowflake':
                config += "ClientTransportPlugin snowflake exec /usr/bin/snowflake-client\n"
            elif bridge_type == 'meek-azure':
                config += "ClientTransportPlugin meek_lite exec /usr/bin/meek-client\n"
            elif bridge_type == 'webtunnel':
                config += "ClientTransportPlugin webtunnel exec /usr/bin/webtunnel-client\n"
                
            for bridge in bridge_lines:
                config += f"{bridge}\n"
                
        config += f"""ExitNodes {{{inst.country}}}
StrictNodes 1
NewCircuitPeriod {circuit_period}
MaxCircuitDirtiness 300
CircuitBuildTimeout {'120' if use_bridges else '60'}
LearnCircuitBuildTimeout 0
NumEntryGuards 3
UseEntryGuards 1
"""
        
        with open(inst.torrc, "w") as f:
            f.write(config)
            
    def find_fastest_ip_for_instance(self, inst, use_bridges=False, max_attempts=3):
        """Find fastest IP for specific instance - like original code"""
        print(f"\n[+] Finding fastest IP for {inst.name} ({inst.country}) - {max_attempts} attempts...")
        
        results = []
        
        for attempt in range(max_attempts):
            print(f"\n--- Attempt {attempt + 1}/{max_attempts} for {inst.name} ---")
            
            # Stop any existing instance
            self.stop_instance(inst)
            
            # Create torrc and start
            self.create_torrc(inst, use_bridges)
            
            # Clean cache
            subprocess.run(f"rm -rf {inst.data_dir}/cached-*", shell=True, capture_output=True)
            subprocess.run(f"rm -rf {inst.data_dir}/state", shell=True, capture_output=True)
            
            # Start Tor
            subprocess.Popen(
                f"tor -f {inst.torrc}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            wait_time = 30 if use_bridges and self.bridge_data and self.bridge_data[1] == 'obfs4' else 20
            print(f"    [+] Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            
            # Test connection
            ip, country, city, ping = self.get_ip_and_location(inst.port)
            
            if ip and country == inst.country:
                print(f"    [+] Testing speed for {ip}...")
                speed = self.test_speed(inst.port)
                
                result = {
                    'ip': ip, 'country': country, 'city': city,
                    'ping': ping, 'speed': speed
                }
                results.append(result)
                
                print(f"    [✓] Success: IP={ip}, Speed={speed} Mbps, Ping={ping}ms")
            else:
                print(f"    [!] Wrong country ({country} vs {inst.country})")
            
            time.sleep(2)
        
        if results:
            # Find best result
            best = max(results, key=lambda x: x.get('speed', 0))
            inst.ip = best['ip']
            inst.city = best['city']
            inst.ping = best['ping']
            inst.speed = best['speed']
            inst.best_results = results
            
            print(f"\n[✓] Best for {inst.name}: {best['ip']} - {best['speed']} Mbps")
            return best
        else:
            print(f"\n[✗] No successful connection for {inst.name}")
            return None
            
    def stop_instance(self, inst):
        """Stop a Tor instance"""
        subprocess.run(f"pkill -f 'tor -f {inst.torrc}'", shell=True, capture_output=True)
        time.sleep(2)
        
    def check_instance_running(self, inst):
        """Check if Tor instance is running"""
        result = subprocess.run(
            f"pgrep -f 'tor -f {inst.torrc}'",
            shell=True,
            capture_output=True
        )
        return result.returncode == 0
        
    def start_all_instances_with_best_ips(self):
        """Start all instances and find best IPs for each"""
        if not self.instances:
            print("[!] No instances configured")
            return
            
        use_bridges = self.bridge_data is not None
        successful = []
        
        print(f"\n[+] Finding fastest IPs for all instances ({self.attempts_per_country} attempts each)...")
        
        for name, inst in self.instances.items():
            result = self.find_fastest_ip_for_instance(inst, use_bridges, self.attempts_per_country)
            if result:
                successful.append({
                    'name': name,
                    'inst': inst,
                    **result
                })
        
        # Sort by speed
        successful.sort(key=lambda x: (-x['speed'], x['ping']))
        
        if successful:
            print(f"\n{'='*70}")
            print("FASTEST IPs (sorted by speed):")
            print(f"{'='*70}")
            
            for i, result in enumerate(successful, 1):
                inst = result['inst']
                
                speed_indicator = ""
                if result['speed'] >= 5:
                    speed_indicator = " (HIGH-SPEED)"
                elif result['speed'] >= 2:
                    speed_indicator = " (FAST)"
                elif result['speed'] >= 0.5:
                    speed_indicator = " (GOOD)"
                
                print(f"{i}. {result['name']} ({inst.country}){speed_indicator}:")
                print(f"   IP: {result['ip']} | City: {result['city']}")
                print(f"   Speed: {result['speed']} Mbps | Ping: {result['ping']}ms")
                print(f"   Proxy: socks5://127.0.0.1:{inst.port}\n")
                
            best = successful[0]
            print(f"[+] BEST: {best['name']} - {best['speed']} Mbps")
            
    def test_all_instances(self):
        """Test all running instances"""
        print(f"\n{'='*60}")
        print(f"TESTING ALL INSTANCES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        results = []
        for name, inst in self.instances.items():
            if self.check_instance_running(inst):
                print(f"\n[+] Testing {name}...")
                ip, country, city, ping = self.get_ip_and_location(inst.port)
                if ip:
                    speed = self.test_speed(inst.port)
                    inst.ip = ip
                    inst.city = city
                    inst.ping = ping
                    inst.speed = speed
                    results.append(inst)
                    print(f"    IP: {ip} | Speed: {speed} Mbps")
            else:
                print(f"\n[!] {name} is not running")
                    
        if results:
            results.sort(key=lambda x: (-x.speed, x.ping))
            print(f"\n{'='*60}")
            print("RESULTS (sorted by speed):")
            print(f"{'='*60}")
            
            for i, inst in enumerate(results, 1):
                print(f"{i}. {inst.name} ({inst.country}):")
                print(f"   IP: {inst.ip} | City: {inst.city}")
                print(f"   Speed: {inst.speed} Mbps | Ping: {inst.ping}ms")
                print(f"   Proxy: socks5://127.0.0.1:{inst.port}")
                
    def configure_bridges(self):
        """Configure bridge settings"""
        print("\n" + "="*50)
        print("BRIDGE CONFIGURATION")
        print("="*50)
        
        print("Examples:")
        print("1. OBFS4:")
        print("   Bridge obfs4 192.95.36.142:443 CDF2E852BF539B82BD549E1A2AC8D80FE2162864")
        print("\n2. SNOWFLAKE:")
        print("   Bridge snowflake 192.0.2.3:80 2B280B23E1107BB62ABFC40DDCC8824814F80A72")
        print("\nGet bridges: https://bridges.torproject.org/")
        print("="*50)
        
        print("\nEnter bridges (one per line, empty line to finish):")
        
        bridge_input = ""
        while True:
            line = input()
            if line.strip() == "":
                if bridge_input.strip():
                    break
            else:
                bridge_input += line + "\n"
        
        if bridge_input.strip():
            self.bridge_data = self.parse_bridge_input(bridge_input)
            if self.bridge_data and self.bridge_data[0]:
                bridge_lines, bridge_type = self.bridge_data
                bridge_count = len(bridge_lines) if isinstance(bridge_lines, list) else 1
                self.save_config()
                print(f"[+] Configured {bridge_count} {bridge_type.upper()} bridge(s)")
        else:
            self.bridge_data = None
            self.save_config()
            print("[+] Bridge configuration cleared")
            
    def list_instances(self):
        """List all configured instances"""
        if not self.instances:
            print("[!] No instances configured")
            return
            
        print("\n" + "="*60)
        print("CONFIGURED TOR INSTANCES")
        print("="*60)
        
        for i, (name, inst) in enumerate(self.instances.items(), 1):
            status = "Active" if self.check_instance_running(inst) else "Stopped"
            print(f"{i}. {name}:")
            print(f"   Country: {inst.country}")
            print(f"   Port: {inst.port}")
            print(f"   Directory: {inst.data_dir}")
            print(f"   Status: {status}")
            if inst.ip:
                print(f"   Current IP: {inst.ip}")
                print(f"   City: {inst.city}")
                print(f"   Speed: {inst.speed} Mbps | Ping: {inst.ping}ms")
            if inst.best_results:
                print(f"   Tested IPs: {len(inst.best_results)}")
            print()
            
    def remove_instance(self):
        """Remove Tor instance"""
        if not self.instances:
            print("[!] No instances to remove")
            return
            
        print("\n" + "="*50)
        print("REMOVE TOR INSTANCE")
        print("="*50)
        
        for i, name in enumerate(self.instances.keys(), 1):
            inst = self.instances[name]
            print(f"{i}. {name} ({inst.country}) - Port {inst.port}")
            
        choice = input("\nEnter instance name to remove: ").strip()
        if choice in self.instances:
            # Stop the instance first
            self.stop_instance(self.instances[choice])
            
            # Ask if user wants to delete data directory
            delete_data = input(f"Delete data directory {self.instances[choice].data_dir}? (y/n): ").strip().lower()
            if delete_data == 'y':
                subprocess.run(f"rm -rf {self.instances[choice].data_dir}", shell=True)
                print(f"[+] Deleted data directory")
                
            del self.instances[choice]
            self.save_config()
            print(f"[+] Removed instance: {choice}")
        else:
            print(f"[!] Instance '{choice}' not found")
            
    def setup_schedule(self):
        """Setup scheduled testing"""
        print("\n" + "="*50)
        print("SCHEDULE CONFIGURATION")
        print("="*50)
        
        print("Enter test interval in hours (e.g., 1, 6, 24)")
        print("Enter 0 to disable scheduling")
        
        try:
            hours = float(input("Hours: ").strip())
            if hours > 0:
                self.test_schedule = hours
                self.save_config()
                print(f"[+] Scheduled testing every {hours} hours")
                return True
            else:
                self.test_schedule = None
                self.save_config()
                print("[+] Scheduling disabled")
                return False
        except ValueError:
            print("[!] Invalid input")
            return False
            
    def run_scheduled_tests(self):
        """Run scheduled tests in background"""
        if not self.test_schedule:
            return
            
        def job():
            print(f"\n[+] Running scheduled test...")
            self.test_all_instances()
            
        schedule.every(self.test_schedule).hours.do(job)
        
        print(f"[+] Starting scheduled tests every {self.test_schedule} hours")
        print("[+] Press Ctrl+C to stop")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n[+] Stopping scheduled tests")
                break
                
    def set_attempts_per_country(self):
        """Set number of attempts per country"""
        print("\n" + "="*50)
        print("SET ATTEMPTS PER COUNTRY")
        print("="*50)
        
        print(f"Current setting: {self.attempts_per_country} attempts")
        
        try:
            attempts = int(input("Enter number of attempts (1-10) [3]: ").strip() or "3")
            if 1 <= attempts <= 10:
                self.attempts_per_country = attempts
                self.save_config()
                print(f"[+] Set to {attempts} attempts per country")
            else:
                print("[!] Invalid number (must be 1-10)")
        except ValueError:
            print("[!] Invalid input")
            
    def auto_start(self):
        """Auto-start with saved configuration"""
        if not self.instances:
            print("[!] No saved configuration found")
            print("[!] Please run in interactive mode first to configure")
            return
            
        print(f"[+] Auto-starting {len(self.instances)} instance(s)...")
        print(f"[+] Testing {self.attempts_per_country} times per instance for best IP...")
        
        self.start_all_instances_with_best_ips()
        
        if self.test_schedule:
            print(f"\n[+] Scheduled testing enabled: every {self.test_schedule} hours")
            self.run_scheduled_tests()
                    
    def interactive_menu(self):
        """Main interactive menu"""
        while True:
            print("\n" + "="*60)
            print("TOR MANAGER - MAIN MENU")
            print("GitHub: https://github.com/AmirForge/TorFleet")
            print("Telegram: https://t.me/dusty_mesa")
            print("="*60)
            print(f"Configured instances: {len(self.instances)}")
            if self.bridge_data:
                print(f"Bridges: {len(self.bridge_data[0])} configured ({self.bridge_data[1]})")
            print(f"Attempts per country: {self.attempts_per_country}")
            if self.test_schedule:
                print(f"Scheduled testing: every {self.test_schedule} hours")
            print("="*60)
            
            print("\n1. Add Tor instance(s)")
            print("2. Remove Tor instance")
            print("3. List instances")
            print("4. Configure bridges")
            print("5. Start all (find best IPs)")
            print("6. Test running instances")
            print("7. Setup scheduling")
            print("8. Run scheduled tests")
            print("9. Set attempts per country")
            print("10. Save and exit")
            print("0. Exit without saving")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                self.add_instance_interactive()
            elif choice == '2':
                self.remove_instance()
            elif choice == '3':
                self.list_instances()
            elif choice == '4':
                self.configure_bridges()
            elif choice == '5':
                self.start_all_instances_with_best_ips()
            elif choice == '6':
                self.test_all_instances()
            elif choice == '7':
                self.setup_schedule()
            elif choice == '8':
                if self.test_schedule:
                    self.run_scheduled_tests()
                else:
                    print("[!] No schedule configured")
            elif choice == '9':
                self.set_attempts_per_country()
            elif choice == '10':
                self.save_config()
                print("[+] Configuration saved. Exiting...")
                break
            elif choice == '0':
                print("[+] Exiting without saving...")
                break
            else:
                print("[!] Invalid choice")

def main():
    parser = argparse.ArgumentParser(description='Tor Manager with Multiple Instances')
    parser.add_argument('-y', '--yes', action='store_true',
                       help='Auto-start with saved configuration')
    parser.add_argument('--add', action='store_true',
                       help='Add new instance')
    parser.add_argument('--list', action='store_true',
                       help='List all instances')
    parser.add_argument('--test', action='store_true',
                       help='Test all instances')
    
    args = parser.parse_args()
    
    manager = TorManager()
    
    if args.yes:
        # Auto-start mode
        manager.auto_start()
    elif args.list:
        manager.list_instances()
    elif args.test:
        manager.test_all_instances()
    elif args.add:
        manager.add_instance_interactive()
        manager.save_config()
    else:
        # Interactive mode
        os.system('clear')
        print("="*60)
        print("TOR MANAGER - Multi-Instance Controller")
        print("="*60)
        manager.interactive_menu()

if __name__ == "__main__":
    main()
