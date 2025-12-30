import os
import shutil
import subprocess
import json
import sys
import time
import urllib.request
import urllib.parse

# Fix for Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_terraform_output(output_name):
    """Fetch server IP dynamically from TF state"""
    try:
        result = subprocess.run(
            ['terraform', 'output', '-json'],
            cwd='./terraform',
            capture_output=True,
            text=True,
            check=True
        )
        outputs = json.loads(result.stdout)
        return outputs[output_name]['value']
    except Exception as e:
        print(f"❌ Terraform error: {e}")
        return None

def load_config():
    # Load local deployment settings
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Prioritize TF output for the host IP
    tf_ip = get_terraform_output('server_public_ip')
    if tf_ip:
        print(f"🌐 Using IP from Terraform: {tf_ip}")
        config["remote_host"] = tf_ip
    else:
        print("⚠️ TF IP not found, falling back to config.json")

    if os.getenv("SSH_KEY_PATH"):
        config["ssh_key_path"] = os.getenv("SSH_KEY_PATH")
    return config

def send_telegram_message(config, text):
    """Notify via Telegram bot"""
    token = config.get("telegram_token")
    chat_id = config.get("telegram_chat_id")
    
    if not token or not chat_id:
        print("⚠️ Telegram credentials missing")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    data = urllib.parse.urlencode(params).encode()
    
    print(f"📱 Sending update to Telegram (ID: {chat_id})...")
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                print("✅ Telegram notification sent!")
    except Exception as e:
        print(f"❌ Telegram notify failed: {e}")

def remote_execute(config, command):
    # Helper for running commands via SSH
    host = config["remote_host"]
    user = config["remote_user"]
    key = config["ssh_key_path"]
    ssh_cmd = ["ssh", "-i", key, "-o", "StrictHostKeyChecking=no", f"{user}@{host}", command]
    return subprocess.run(ssh_cmd, capture_output=True, text=True)

def setup_remote_network(network_name, config):
    # Ensure Docker network exists on the host
    res = remote_execute(config, "docker network ls")
    if network_name not in res.stdout:
        remote_execute(config, f"docker network create {network_name}")

def build_and_push_image(config):
    # Standard Docker build/push flow
    image_name = config["project_name"]
    version = config["version"]
    docker_user = config["docker_user"]
    full_tag = f"{docker_user}/{image_name}:{version}"
    latest_tag = f"{docker_user}/{image_name}:latest"
    
    print(f"--- 1. Building & Pushing: {full_tag} ---")
    try:
        subprocess.run(["docker", "build", "-t", full_tag, "-t", latest_tag, "."], check=True)
        subprocess.run(["docker", "push", full_tag], check=True)
        subprocess.run(["docker", "push", latest_tag], check=True)
        return True
    except Exception as e:
        print(f"❌ Build failed: {e}")
        send_telegram_message(config, f"❌ *Build Error:* {image_name}:{version}")
        return False

def verify_deployment(url):
    # Simple endpoint check
    print(f"--- 4. Verifying Deployment at {url} ---")
    for i in range(5):
        try:
            response = urllib.request.urlopen(url, timeout=5)
            if response.getcode() == 200:
                print("✅ HEALTH CHECK PASSED!")
                return True
        except:
            print(f"   Waiting for Nginx... (Attempt {i+1})")
            time.sleep(3)
    return False

def run_system_remote(config):
    # Main deployment logic on the remote instance
    image_name = config["project_name"]
    version = config["version"]
    docker_user = config["docker_user"]
    port = config["external_port"]
    network_name = "deployer-network"
    
    full_image_name = f"{docker_user}/{image_name}:{version}"
    app_container = f"{image_name}-container"
    proxy_name = "my-proxy-server"
    
    print(f"--- 3. Deploying to Remote Server: {config['remote_host']} ---")
    
    # Cleanup old instances
    remote_execute(config, f"docker stop {app_container} {proxy_name}")
    remote_execute(config, f"docker rm -f {app_container} {proxy_name}")
    
    # Pull fresh image from Hub
    remote_execute(config, f"docker pull {full_image_name}")
    
    # Start App
    remote_execute(config, f"docker run -d --name {app_container} --network {network_name} {full_image_name}")
    
    # Start Proxy (Nginx) with inline config
    proxy_cmd = (
        f"docker run -d --name {proxy_name} --network {network_name} -p {port}:80 "
        f"nginx:alpine sh -c \"echo 'server {{ listen 80; location / {{ proxy_pass http://{app_container}; }} }}' "
        f"> /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'\""
    )
    remote_execute(config, proxy_cmd)
    
    # Final check and notification
    site_url = f"http://{config['remote_host']}:{port}"
    if verify_deployment(site_url):
        msg = f"🚀 *Deploy Success!*\n📦 Project: `{image_name}`\n🔢 Version: `{version}`\n🌐 URL: {site_url}"
        send_telegram_message(config, msg)
    else:
        send_telegram_message(config, f"⚠️ Deploy finished but *Health Check failed* for {site_url}")

if __name__ == "__main__":
    # Script entry point
    config = load_config()
    if build_and_push_image(config):
        setup_remote_network("deployer-network", config)
        run_system_remote(config)