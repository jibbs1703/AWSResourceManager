# AWS Resource Manager
![Python Version](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)
![aws_resource_manager](https://img.shields.io/badge/aws_resource_manager-unreleased-yellow)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)

## Overview

The aws_resource_manager is a custom Python package designed to simplify the management of AWS resources.
It provides a unified interface for interacting with various AWS services, making it easier to automate 
tasks and manage infrastructure.

The package is built majorly on the [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
library and includes custom modules for managing EC2 instances and S3 buckets with elaborate logging and error
handling capabilities.

The package was built in support of an in-house project but is also designed with some extensibility in mind, 
allowing other users to easily add support for additional AWS services as needed in their projects.

## Features

### S3

- **Bucket Management:** Create, delete, and list S3 buckets.
- **Object Management:** Upload, download, and delete objects in S3 buckets.
- **Presigned URLs:** Generate presigned URLs for secure access to S3 objects.

### EC2

- **Instance Management:** Launch, stop, and terminate EC2 instances.
- **Key Pair Management:** Create and manage EC2 key pairs.
- **Security Group Management:** Create and manage security groups for EC2 instances.

## Getting Started

- **Clone Repository:**
```bash
git clone https://github.com/your-username/AWS-Resource-Manager.git
cd AWS-Resource-Manager
```

- **Create and Activate Virtual Environment:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

- **Install Project Requirements:**
```bash
pip install -r requirements.txt
```

- **Build Package:**
```bash
python -m build
```

- **Install Package:**
```bash
pip install .
```
