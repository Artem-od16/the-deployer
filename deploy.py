import os
import shutil
import subprocess
import json
import sys
import time
import urllib.request

# Фикс кодировки для Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    if os.getenv("SSH_KEY_PATH"):
        config["ssh_key_path"] = os.getenv("SSH_KEY_PATH")
    return config

def remote_execute(config, command):
    host = config["remote_host"]
    user = config["remote_user"]
    key = config["ssh_key_path"]
    ssh_cmd = ["ssh", "-i", key, "-o", "StrictHostKeyChecking=no", f"{user}@{host}", command]
    return subprocess.run(ssh_cmd, check=True, capture_output=True, text=True)

def setup_remote_network(network_name, config):
    try:
        res = remote_execute(config, "docker network ls")
        if network_name not in res.stdout:
            remote_execute(config, f"docker network create {network_name}")
    except Exception as e:
        print(f"Network error: {e}")

def build_and_push_image(config):
    image_name = config["project_name"]
    version = config["version"]
    docker_user = config["docker_user"]
    full_tag = f"{docker_user}/{image_name}:{version}"
    latest_tag = f"{docker_user}/{image_name}:latest"
    
    print(f"--- Building & Pushing: {full_tag} ---")
    try:
        subprocess.run(["docker", "build", "-t", full_tag, "-t", latest_tag, "."], check=True)
        subprocess.run(["docker", "push", full_tag], check=True)
        subprocess.run(["docker", "push", latest_tag], check=True)
        return True
    except Exception as e:
        print(f"Build failed: {e}")
        return False

def verify_deployment(url):
    print(f"--- Checking {url} ---")
    for i in range(5):
        try:
            response = urllib.request.urlopen(url, timeout=5)
            if response.getcode() == 200:
                return True
        except:
            time.sleep(3)
    return False

def run_system_remote(config):
    image_name = config["project_name"]
    version = config["version"]
    docker_user = config["docker_user"]
    port = config["external_port"]
    network_name = "deployer-network"
    
    full_image_name = f"{docker_user}/{image_name}:{version}"
    app_container = f"{image_name}-container"
    proxy_name = "my-proxy-server"
    
    try:
        # ОЧИСТКА: Удаляем старые контейнеры полностью
        remote_execute(config, f"docker rm -f {app_container} {proxy_name} || true")
        remote_execute(config, f"docker pull {full_image_name}")
        
        # ЗАПУСК ПРИЛОЖЕНИЯ
        remote_execute(config, f"docker run -d --name {app_container} --network {network_name} {full_image_name}")
        
        # ЗАПУСК ПРОКСИ (с принудительным перенаправлением на приложение)
        proxy_cmd = (
            f"docker run -d --name {proxy_name} --network {network_name} -p {port}:80 "
            f"nginx:alpine sh -c \"echo 'server {{ listen 80; location / {{ proxy_pass http://{app_container}; }} }}' "
            f"> /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'\""
        )
        remote_execute(config, proxy_cmd)
        
        site_url = f"http://{config['remote_host']}"
        if verify_deployment(site_url):
            print(f"🚀 SUCCESS: {site_url}")
    except Exception as e:
        print(f"Deployment error: {e}")

if __name__ == "__main__":
    config = load_config()
    if build_and_push_image(config):
        setup_remote_network("deployer-network", config)
        run_system_remote(config)