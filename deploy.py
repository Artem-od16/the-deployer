import os
import subprocess
import json
import time
import urllib.request
import urllib.parse

def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    mapping = {
        "REMOTE_HOST": "remote_host",
        "TELEGRAM_TOKEN": "telegram_token",
        "TELEGRAM_CHAT_ID": "telegram_chat_id"
    }
    for env_name, config_key in mapping.items():
        if os.getenv(env_name):
            config[config_key] = os.getenv(env_name)
    return config

def send_telegram_message(config, text):
    token = config.get("telegram_token")
    chat_id = config.get("telegram_chat_id")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {"chat_id": chat_id, "text": text}
    data = urllib.parse.urlencode(params).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data))
        print("Success: Telegram notification sent")
    except Exception as e:
        print(f"Error: Telegram failed: {e}")

def build_and_push(config):
    tag = f"{config['docker_user']}/{config['project_name']}:{config['version']}"
    subprocess.run(["docker", "build", "-t", tag, "."], check=True)
    subprocess.run(["docker", "push", tag], check=True)
    return tag

def deploy_remote(config, image):
    host = config["remote_host"]
    user = config["remote_user"]
    key = config["ssh_key_path"]
    container = f"{config['project_name']}-container"
    
    # HARD RESET: stop everything, remove everything, then run
    commands = [
        f"sudo fuser -k 80/tcp || true",
        f"docker rm -f $(docker ps -aq) || true",
        f"docker system prune -f || true",
        f"docker pull {image}",
        f"docker run -d --name {container} -p 80:80 {image}"
    ]
    
    for cmd in commands:
        ssh_cmd = ["ssh", "-i", key, "-o", "StrictHostKeyChecking=no", f"{user}@{host}", cmd]
        subprocess.run(ssh_cmd)
    
    print("Deployment finished. Waiting for Nginx to start...")
    time.sleep(10) # Increased wait time for stability
    send_telegram_message(config, f"✅ Deployment Ready! \nURL: http://{host}")

if __name__ == "__main__":
    conf = load_config()
    img_tag = build_and_push(conf)
    deploy_remote(conf, img_tag)