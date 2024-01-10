#infrastrcutre_monitoring_mongodb.py

import socket
import telnetlib
import requests
from datetime import datetime
import psutil
from pymongo import MongoClient
import paramiko

# MongoDB Configuration
MONGODB_URI = "your_mongodb_uri" #replace with your mongodb credentials
DB_NAME = "mongodb_name_example-monitoring-tools" #repace with your mongodb collection

# Remote Server Configuration
REMOTE_SERVER_IP = "example.ip.address.it"  # Website Remote Server IP, replace
REMOTE_SERVER_SSH_PORT = 22  # SSH Port, replace
REMOTE_SERVER_SSH_USER = "example_username"  # SSH Username, replace
REMOTE_SERVER_SSH_PASSWORD = "example_password" #SSH Password, replace

# Initialize MongoDB connection and create a collection
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

def log_to_mongodb(collection_name, status):
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    collection = db[collection_name]
    log_entry = {
        "timestamp": timestamp,
        "status": status
    }
    collection.insert_one(log_entry)

def check_dns(url):
    try:
        # Check DNS resolution for the website
        socket.gethostbyname(url)
        log_to_mongodb('DNS', 'Success')
        return True
    except socket.error as e:
        log_to_mongodb('DNS', f'Failed: {str(e)}')
        return False

def check_website_health(url):
    try:
        # Check DNS resolution
        if not check_dns(url):
            log_to_mongodb('WEBSITE', f'DNS resolution failed for {url}')
            return False

        # Check HTTP response
        response = requests.get(f"http://{url}")
        response.raise_for_status()
        log_to_mongodb('WEBSITE', 'Success')
        return True
    except requests.RequestException as e:
        log_to_mongodb('WEBSITE', f'Website Health Check Error: {str(e)}')
        return False

def check_telnet_service(url, port, expected_response, collection_name):
    try:
        with telnetlib.Telnet(url, port, timeout=5) as tn:
            tn.read_until(expected_response.encode(), timeout=5)
            log_to_mongodb(collection_name, 'Success')
            return True
    except Exception as e:
        log_to_mongodb(collection_name, f'Failed: {str(e)}')
        return False

def check_ftp_service(url, port=21):
    return check_telnet_service(url, port, '220', 'FTP')

def check_ssh_service(url, port=22):
    return check_telnet_service(url, port, 'SSH', 'SSH')

def check_remote_system_health():
    try:
        # SSH into the remote server and get system information
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(REMOTE_SERVER_IP, port=REMOTE_SERVER_SSH_PORT, username=REMOTE_SERVER_SSH_USER, password=REMOTE_SERVER_SSH_PASSWORD)

        # Get CPU usage, memory usage, and disk space on the remote server
        _, stdout, _ = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
        cpu_usage = float(stdout.read().decode().strip())

        _, stdout, _ = ssh.exec_command("free | awk '/Mem/{print $3/$2 * 100}'")
        memory_usage = float(stdout.read().decode().strip())

        _, stdout, _ = ssh.exec_command("df -h / | awk '/\//{print $5}'")
        disk_usage = float(stdout.read().decode().strip().replace('%', ''))

        log_to_mongodb('SERVER', f'Success - CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%')

        ssh.close()
        return True

    except Exception as e:
        log_to_mongodb('SERVER', f'Failed: {str(e)}')
        return False

def main():
    website_url = "website_domain.example" #replace with your domain

    try:
        if check_website_health(website_url):
            print("Website is healthy.")
        else:
            # Trigger incident response
            # Add code to escalate the incident (e.g., send notifications, log the incident)
            print("Incident detected. Initiating automated response.")

        if check_ftp_service(website_url):
            print("FTP service is healthy.")
        else:
            # Trigger incident response
            # Add code to escalate the incident (e.g., send notifications, log the incident)
            print("FTP service incident detected. Initiating automated response.")

        if check_ssh_service(website_url):
            print("SSH service is healthy.")
        else:
            # Trigger incident response
            # Add code to escalate the incident (e.g., send notifications, log the incident)
            print("SSH service incident detected. Initiating automated response.")

        if check_remote_system_health():
            print("Server system is healthy.")
        else:
            # Trigger incident response
            # Add code to escalate the incident (e.g., send notifications, log the incident)
            print("Server system incident detected. Initiating automated response.")

    except Exception as e:
        # Handle exceptions and escalate the incident
        log_to_mongodb('GENERAL', f'Error: {str(e)}. Escalating incident.')
        # Add code to escalate the incident (e.g., send notifications, log the incident)

    finally:
        # Close MongoDB connection
        client.close()
        
if __name__ == "__main__":
    main()

