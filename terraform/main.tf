# 1. Provider configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# 2. Connection setup for AWS
provider "aws" {
  region = "eu-west-3" # Using Paris region for low latency
}

# 3. Compute resources - EC2 Instance
resource "aws_instance" "app_server" {
  ami           = "ami-0ef9bcd5dfb57b968" # Ubuntu Server 22.04 LTS
  instance_type = "t3.micro"              # Using t3.micro for cost-efficiency
  key_name      = "aws-paris-key"         # Pre-configured SSH key

  # Reference existing security group to allow 22/80/8081 ports
  vpc_security_group_ids = ["sg-08b927f5c1af78740"] 
  
  tags = {
    Name = "The-Deployer-Managed-Server"
    Env  = "Dev"
  }
}

# 4. Outputs for deployment script
output "server_public_ip" {
  description = "Public IP address used by deploy.py for automation"
  value       = aws_instance.app_server.public_ip
}