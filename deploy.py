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
        return json.load(f)

def remote_execute(config, command):
    host = config["remote_host"]
    user = config["remote_user"]
    key = config["ssh_key_path"]
    ssh_cmd = ["ssh", "-i", key, "-o", "StrictHostKeyChecking=no", f"{user}@{host}", command]
    return subprocess.run(ssh_cmd, check=True, capture_output=True, text=True)

def setup_remote_network(network_name, config):
    print(f"--- Checking remote network: {network_name} ---")
    try:
        res = remote_execute(config, "docker network ls")
        if network_name not in res.stdout:
            remote_execute(config, f"docker network create {network_name}")
            print(f"SUCCESS: Network '{network_name}' created.")
        else:
            print("Network exists.")
    except Exception as e:
        print(f"Network check error: {e}")

def build_and_push_image(config):
    image_name = config["project_name"]
    version = config["version"]
    docker_user = config["docker_user"]
    
    full_tag = f"{docker_user}/{image_name}:{version}"
    latest_tag = f"{docker_user}/{image_name}:latest"
    
    print(f"--- 1. Building Image LOCALLY: {full_tag} ---")
    
    if not os.path.exists("Dockerfile"):
         with open("Dockerfile", "w") as f:
            f.write("FROM nginx:alpine\nCOPY . /usr/share/nginx/html")
    
    try:
        subprocess.run(["docker", "build", "-t", full_tag, "-t", latest_tag, "."], check=True)
        print(f"--- 2. Pushing to Docker Hub ---")
        subprocess.run(["docker", "push", full_tag], check=True)
        subprocess.run(["docker", "push", latest_tag], check=True)
        print("✅ Image is in the cloud.")
        return True
    except Exception as e:
        print(f"❌ Build/Push failed: {e}")
        return False

def verify_deployment(url, attempts=5):
    """ Проверяет, отвечает ли сайт кодом 200 """
    print(f"--- 4. Verifying Deployment at {url} ---")
    for i in range(attempts):
        try:
            response = urllib.request.urlopen(url, timeout=5)
            if response.getcode() == 200:
                print(f"✅ HEALTH CHECK PASSED! Site is live (Attempt {i+1}).")
                return True
        except Exception:
            print(f"   [...] Waiting for site to wake up... (Attempt {i+1}/{attempts})")
            time.sleep(3)
    print("❌ HEALTH CHECK FAILED: Site is not responding correctly.")
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
    
    print(f"--- 3. Deploying to Remote Server ({config['remote_host']}) ---")
    
    try:
        print(f"Pulling {full_image_name}...")
        remote_execute(config, f"docker pull {full_image_name}")
        remote_execute(config, f"docker rm -f {app_container} {proxy_name} || true")
        
        print("Starting App Container...")
        remote_execute(config, f"docker run -d --name {app_container} --network {network_name} {full_image_name}")
        
        print("Starting Nginx Proxy...")
        proxy_cmd = (
            f"docker run -d --name {proxy_name} --network {network_name} -p {port}:80 "
            f"nginx:alpine sh -c \"echo 'server {{ listen 80; location / {{ proxy_pass http://{app_container}; }} }}' "
            f"> /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'\""
        )
        remote_execute(config, proxy_cmd)
        
        # Запускаем проверку
        site_url = f"http://{config['remote_host']}:{port}"
        if verify_deployment(site_url):
            print(f"🚀 DEPLOYED SUCCESSFULLY! {site_url}")
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    config = load_config()
    
    if len(sys.argv) > 1 and sys.argv[1] == "logs":
        res = remote_execute(config, "docker logs my-proxy-server")
        print(res.stdout)
    else:
        # Увеличим версию для теста
        print(f"Starting Deployer for {config['project_name']} v.{config['version']}")
        
        if build_and_push_image(config):
            setup_remote_network("deployer-network", config)
            run_system_remote(config)