#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

def run(cmd, check=True):
    print(f"[+] Running: {cmd}")
    result = subprocess.run(
        cmd, shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if check and result.returncode != 0:
        print(f"[-] Command failed: {cmd}")
        print(result.stderr)
        return result
    return result

# ----------------------------
# Ensure root
# ----------------------------
if os.geteuid() != 0:
    print("❌ Run this script as root!")
    sys.exit(1)

print(f"=== Ansible Installer for {os.getenv('PRETTY_NAME', 'RHEL 10')} ===")

# ----------------------------
# 1. Install Ansible (RHEL 10 Logic)
# ----------------------------
print("[*] Attempting to install ansible-core from local AppStream...")
# In RHEL 10, the package is often named 'ansible-core'
res = run("dnf install -y ansible-core", check=False)

if res.returncode != 0:
    print("[!] ansible-core not found. Trying 'ansible'...")
    res = run("dnf install -y ansible", check=False)

if res.returncode != 0:
    print("[!] DNF installation failed. Attempting PIP3 (requires python3-pip)...")
    run("dnf install -y python3-pip")
    run("pip3 install ansible")

# ----------------------------
# 2. Prepare directories
# ----------------------------
ansible_dir = "/root/.ansible"
os.makedirs(ansible_dir, exist_ok=True)

# ----------------------------
# 3. Copy Files (Corrected Paths)
# ----------------------------
base_repo_path = "/root/openShift_Cluster_Config/service_Node_Config/svc-1/config_Files/ansible"

# Copy ansible.cfg
repo_cfg = os.path.join(base_repo_path, "ansible.cfg")
dest_cfg = "/root/.ansible.cfg"

if os.path.exists(repo_cfg):
    shutil.copy(repo_cfg, dest_cfg)
    print(f"[+] ansible.cfg copied → {dest_cfg}")
else:
    print(f"❌ Error: Source config not found at {repo_cfg}")

# Copy inventory
repo_hosts = os.path.join(base_repo_path, "hosts")
dest_hosts = os.path.join(ansible_dir, "hosts")

if os.path.exists(repo_hosts):
    shutil.copy(repo_hosts, dest_hosts)
    print(f"[+] Hosts copied → {dest_hosts}")
else:
    print("[*] No hosts file found in repo, creating default")
    with open(dest_hosts, "w") as f:
        f.write("[all]\nlocalhost ansible_connection=local\n")

# ----------------------------
# 4. Verify Ansible
# ----------------------------
print("\n[*] Verifying installation...")
# Ensure we check the version to confirm it's working
run("ansible --version")
result = run("ansible localhost -m ping", check=False)

if result.returncode == 0:
    print("[+] ✅ Ansible is fully operational.")
else:
    print("[-] ❌ Ping test failed. Check your local repo or python environment.")
    sys.exit(1)

print("\n🎉 Setup Complete for RHEL 10!")
