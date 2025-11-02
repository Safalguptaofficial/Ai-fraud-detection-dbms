#!/usr/bin/env python3
"""
Comprehensive System Health Check
Tests backend, databases, and frontend status
"""

import sys
import os
import subprocess
import json
import requests
from datetime import datetime
from typing import Dict, List

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_status(name: str, status: bool, details: str = ""):
    symbol = "✓" if status else "✗"
    color = GREEN if status else RED
    print(f"{color}{symbol} {name}{RESET} {details}")

def check_backend_api() -> Dict:
    """Check if backend API is running and responding"""
    results = {
        "running": False,
        "health_endpoint": False,
        "docs_endpoint": False,
        "port": False,
        "details": []
    }
    
    try:
        # Check if port 8000 is in use
        result = subprocess.run(
            ["lsof", "-ti", ":8000"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            results["port"] = True
            results["details"].append("Port 8000 is in use")
        else:
            results["details"].append("Port 8000 is not in use")
            return results
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/healthz", timeout=5)
            if response.status_code == 200:
                results["health_endpoint"] = True
                results["details"].append(f"Health endpoint: {response.json()}")
            else:
                results["details"].append(f"Health endpoint returned: {response.status_code}")
        except Exception as e:
            results["details"].append(f"Health endpoint error: {str(e)}")
        
        # Test docs endpoint
        try:
            response = requests.get("http://localhost:8000/docs", timeout=5)
            if response.status_code == 200:
                results["docs_endpoint"] = True
                results["details"].append("API docs accessible")
        except Exception as e:
            results["details"].append(f"Docs endpoint error: {str(e)}")
        
        results["running"] = results["port"] and (results["health_endpoint"] or results["docs_endpoint"])
        
    except Exception as e:
        results["details"].append(f"Error checking backend: {str(e)}")
    
    return results

def check_databases() -> Dict:
    """Check database containers and connectivity"""
    results = {
        "postgres": {"container": False, "connection": False, "details": []},
        "oracle": {"container": False, "connection": False, "details": []},
        "mongo": {"container": False, "connection": False, "details": []},
        "redis": {"container": False, "connection": False, "details": []}
    }
    
    try:
        # Check Docker containers
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            containers = result.stdout.strip().split('\n')
            
            # PostgreSQL
            if "postgres" in str(containers):
                results["postgres"]["container"] = True
                # Test connection
                try:
                    test_result = subprocess.run(
                        ["docker", "exec", "fraud-dbms_postgres_1", "pg_isready", "-U", "postgres"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if test_result.returncode == 0:
                        results["postgres"]["connection"] = True
                        results["postgres"]["details"].append("Container healthy")
                except Exception as e:
                    results["postgres"]["details"].append(f"Connection test failed: {str(e)}")
            else:
                results["postgres"]["details"].append("Container not running")
            
            # MongoDB
            if "mongo" in str(containers):
                results["mongo"]["container"] = True
                try:
                    test_result = subprocess.run(
                        ["docker", "exec", "fraud-dbms_mongo_1", "mongosh", "--eval", "db.adminCommand('ping')"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if test_result.returncode == 0 or "ok" in test_result.stdout.lower():
                        results["mongo"]["connection"] = True
                        results["mongo"]["details"].append("Container healthy")
                except Exception as e:
                    results["mongo"]["details"].append(f"Connection test failed: {str(e)}")
            else:
                results["mongo"]["details"].append("Container not running")
            
            # Oracle
            if "oracle" in str(containers):
                results["oracle"]["container"] = True
                try:
                    test_result = subprocess.run(
                        ["docker", "exec", "fraud-dbms_oracle_1", "sqlplus", "-S", "system/password@XE"],
                        input="SELECT 1 FROM DUAL;\nEXIT;\n",
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if test_result.returncode == 0 or "1" in test_result.stdout:
                        results["oracle"]["connection"] = True
                        results["oracle"]["details"].append("Container healthy")
                except Exception as e:
                    results["oracle"]["details"].append(f"Connection test failed: {str(e)}")
            else:
                results["oracle"]["details"].append("Container not running")
            
            # Redis
            if "redis" in str(containers):
                results["redis"]["container"] = True
                try:
                    test_result = subprocess.run(
                        ["docker", "exec", "fraud-dbms_redis_1", "redis-cli", "ping"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if test_result.returncode == 0 and "PONG" in test_result.stdout:
                        results["redis"]["connection"] = True
                        results["redis"]["details"].append("Container healthy")
                except Exception as e:
                    results["redis"]["details"].append(f"Connection test failed: {str(e)}")
            else:
                results["redis"]["details"].append("Container not running")
        else:
            results["postgres"]["details"].append("Docker not accessible")
            results["mongo"]["details"].append("Docker not accessible")
            results["oracle"]["details"].append("Docker not accessible")
            results["redis"]["details"].append("Docker not accessible")
            
    except Exception as e:
        results["postgres"]["details"].append(f"Error: {str(e)}")
    
    return results

def check_frontend() -> Dict:
    """Check if frontend is running"""
    results = {
        "running": False,
        "port": False,
        "accessible": False,
        "dependencies": False,
        "details": []
    }
    
    try:
        # Check if port 3000 is in use
        result = subprocess.run(
            ["lsof", "-ti", ":3000"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            results["port"] = True
            results["details"].append("Port 3000 is in use")
        else:
            results["details"].append("Port 3000 is not in use")
            return results
        
        # Test if frontend is accessible
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code in [200, 307, 308]:  # 307/308 are redirects, also OK
                results["accessible"] = True
                results["details"].append("Frontend is accessible")
            else:
                results["details"].append(f"Frontend returned: {response.status_code}")
        except Exception as e:
            results["details"].append(f"Frontend error: {str(e)}")
        
        # Check dependencies
        web_dir = os.path.join(os.path.dirname(__file__), "apps", "web")
        node_modules = os.path.join(web_dir, "node_modules")
        if os.path.exists(node_modules):
            results["dependencies"] = True
            results["details"].append("Node modules installed")
        else:
            results["details"].append("Node modules not found")
        
        results["running"] = results["port"] and results["accessible"]
        
    except Exception as e:
        results["details"].append(f"Error checking frontend: {str(e)}")
    
    return results

def check_backend_dependencies() -> Dict:
    """Check backend Python dependencies"""
    results = {
        "venv_exists": False,
        "requirements": False,
        "details": []
    }
    
    try:
        api_dir = os.path.join(os.path.dirname(__file__), "services", "api")
        venv_dir = os.path.join(api_dir, "venv")
        requirements_file = os.path.join(api_dir, "requirements.txt")
        
        if os.path.exists(venv_dir):
            results["venv_exists"] = True
            results["details"].append("Virtual environment exists")
        else:
            results["details"].append("Virtual environment not found")
        
        if os.path.exists(requirements_file):
            results["requirements"] = True
            results["details"].append("requirements.txt exists")
        else:
            results["details"].append("requirements.txt not found")
            
    except Exception as e:
        results["details"].append(f"Error: {str(e)}")
    
    return results

def main():
    print_header("SYSTEM HEALTH CHECK")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    overall_status = True
    
    # Check Backend API
    print_header("BACKEND API STATUS")
    backend = check_backend_api()
    print_status("Backend Running", backend["running"])
    print_status("Port 8000 Active", backend["port"])
    print_status("Health Endpoint", backend["health_endpoint"])
    print_status("API Docs", backend["docs_endpoint"])
    for detail in backend["details"]:
        print(f"  {YELLOW}→{RESET} {detail}")
    
    if not backend["running"]:
        overall_status = False
    
    # Check Databases
    print_header("DATABASE STATUS")
    databases = check_databases()
    
    for db_name, db_status in databases.items():
        container_ok = db_status["container"]
        connection_ok = db_status["connection"]
        all_ok = container_ok and connection_ok
        print_status(f"{db_name.upper()} Container", container_ok)
        print_status(f"{db_name.upper()} Connection", connection_ok)
        for detail in db_status["details"]:
            print(f"  {YELLOW}→{RESET} {detail}")
        if not all_ok:
            overall_status = False
    
    # Check Frontend
    print_header("FRONTEND STATUS")
    frontend = check_frontend()
    print_status("Frontend Running", frontend["running"])
    print_status("Port 3000 Active", frontend["port"])
    print_status("Frontend Accessible", frontend["accessible"])
    print_status("Dependencies Installed", frontend["dependencies"])
    for detail in frontend["details"]:
        print(f"  {YELLOW}→{RESET} {detail}")
    
    if not frontend["running"]:
        overall_status = False
    
    # Check Backend Dependencies
    print_header("BACKEND DEPENDENCIES")
    deps = check_backend_dependencies()
    print_status("Virtual Environment", deps["venv_exists"])
    print_status("Requirements File", deps["requirements"])
    for detail in deps["details"]:
        print(f"  {YELLOW}→{RESET} {detail}")
    
    # Final Summary
    print_header("OVERALL STATUS")
    if overall_status:
        print(f"{GREEN}✓ ALL SYSTEMS OPERATIONAL{RESET}")
        print(f"\n{GREEN}Backend:{RESET} http://localhost:8000")
        print(f"{GREEN}Frontend:{RESET} http://localhost:3000")
        print(f"{GREEN}API Docs:{RESET} http://localhost:8000/docs")
    else:
        print(f"{RED}✗ SOME ISSUES DETECTED{RESET}")
        print(f"\n{YELLOW}Please review the details above and fix any issues.{RESET}")
    
    print()

if __name__ == "__main__":
    main()

