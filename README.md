🚀 The Deployer: Automated Infrastructure & CI/CD Pipeline
A production-ready automation tool designed to provision cloud infrastructure and deploy containerized web applications with real-time monitoring and ChatOps integration.

🎯 Project Overview
This project demonstrates a complete DevOps lifecycle. It automates the transition from infrastructure provisioning to application deployment, replacing manual tasks with a robust Python-based orchestrator.

🛠 Tech Stack
Infrastructure: AWS (EC2, Security Groups) provisioned via Terraform.

Containerization: Docker for application packaging and Nginx as a reverse proxy.

Orchestration: Custom Python script for automated Build, Push, and Deploy cycles.

Notification: Telegram Bot API for real-time deployment status (ChatOps).

Environment: Developed and tested on Ubuntu 22.04 LTS.

🏗 Architecture & Workflow
Infrastructure as Code: Terraform scripts define the AWS resources and output the public IP dynamically.

Automated Workflow:

Cleanup: Removes local build artifacts to ensure a fresh environment.

Image Management: Builds Docker images and pushes them to Docker Hub.

Remote Deployment: Connects to the AWS instance via SSH to pull the latest image and restart services.

Health Check: Automatically verifies if the web service is reachable after deployment.

Monitoring: Sends a detailed summary report to Telegram once the deployment is verified.

🚀 How to Use
📋 Prerequisites
Before you begin, ensure you have the following installed:

Terraform (v1.0+)

Docker & Docker Hub account

Python 3.10+ (no extra libraries needed - uses standard modules)

AWS CLI configured or access keys ready

SSH Client (installed by default on Linux/Mac/Windows 10+)

Telegram Bot (via @BotFather) for notifications

1. Provision Infrastructure
cd terraform terraform init terraform apply

2. Configure Environment
Secrets: Rename config.example.json to config.json.

Details: Populate config.json with your AWS credentials, Docker Hub login, and Telegram Bot token.

SSH Key: Place your AWS .pem key in the project root or specify its path in the config.

3. Run Deployment
python deploy.py

🔒 Security & Best Practices
Secrets Management: Sensitive data is managed via config.json, which is strictly excluded from Git tracking.

Access Control: Remote server access is managed through secure .pem key pairs via SSH.

Clean Repository: All temporary artifacts, cache files, and Terraform state files are ignored via a comprehensive .gitignore.




[Full Project Roadmap can be found here](./ROADMAP.md)

Author: Artem Prysiazhnyi