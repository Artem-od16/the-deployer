🗺 Project Roadmap: The Deployer
✅ Phase 1: Local Management & Build (Core Logic)
1.1 Validation & Workspace Prep: Clean builds, artifact management via shutil. [COMPLETED]

1.2 Image Management: Automated Docker build and tagging (v1, v2, latest). [COMPLETED]

1.3 Windows/Linux Compatibility: Fixed encoding issues and path handling for cross-platform execution. [COMPLETED]

✅ Phase 2: Cloud Infrastructure (IaC)
2.1 Terraform Integration: Automated AWS EC2 instance and Security Group provisioning. [COMPLETED]

2.2 Dynamic Inventory: Python script now pulls the server IP directly from Terraform outputs. [COMPLETED]

✅ Phase 3: Remote Orchestration & Security
3.1 SSH Execution: Custom remote_execute logic using native SSH clients and .pem keys. [COMPLETED]

3.2 Docker Hub Integration: Automatic push from local machine and pull on the remote server. [COMPLETED]

3.3 Network Isolation: Automated creation of Docker bridge networks on the remote host. [COMPLETED]

✅ Phase 4: Production-Ready Features (ChatOps & Proxy)
4.1 Reverse Proxy: Nginx integration with dynamic config injection to handle traffic. [COMPLETED]

4.2 Health Checks: Automated verification of the web service availability after deployment. [COMPLETED]

4.3 Telegram Integration: Real-time status updates and error reporting via Telegram Bot API. [COMPLETED]

🚀 Phase 5: Reliability & Advanced DevOps (CURRENT FOCUS)
Step 5.1: Secrets Management: Move from config.json to Environment Variables or AWS Secrets Manager for better security.

Step 5.2: Rollback System: Implement a command to instantly switch to a previous Docker image tag if a health check fails.

Step 5.3: Persistence: Add Docker Volumes to the Nginx/App containers so data isn't lost on restart.

☁️ Phase 6: Scaling & Monitoring
Step 6.1: Monitoring Stack: Add Prometheus/Grafana or a simple Python-based resource monitor (CPU/RAM).

Step 6.2: CI/CD Pipeline: Move the Python script execution into GitHub Actions, so the deploy starts automatically on git push.

Step 6.3: Multiple Environments: Support for dev, staging, and prod environments via Terraform workspaces.