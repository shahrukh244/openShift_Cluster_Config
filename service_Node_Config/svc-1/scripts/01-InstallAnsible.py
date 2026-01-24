#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import hashlib

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

print(f"=== Ansible Installer for {os.getenv('PRETTY_NAME', 'RHEL 9.7')} ===")

def get_ansible_version():
    res = run("ansible --version", check=False)
    if res.returncode != 0:
        return None
    return res.stdout.splitlines()[0]

installed = get_ansible_version()

if installed:
    print(f"[i] Ansible already present: {installed}")
else:
    print("[i] Ansible not installed, will install.")

# Enforce supported version for OpenShift
if installed:
    if "2.14" not in installed:
        print("❌ Installed Ansible version is not supported for OpenShift 4.16")
        print(f"   Detected: {installed}")
        print("   Required: ansible-core 2.14.x")
        sys.exit(1)
    else:
        print("[+] Ansible version is supported for OpenShift.")

# ----------------------------
# 1. Install Ansible (Idempotent)
# ----------------------------
if not installed:
    print("[*] Installing ansible-core from local AppStream...")
    res = run("dnf install -y ansible-core", check=False)

    if res.returncode != 0:
        print("[!] ansible-core not found. Trying 'ansible'...")
        res = run("dnf install -y ansible", check=False)

    if res.returncode != 0:
        print("❌ Installation failed from local repos.")
        sys.exit(1)
else:
    print("[+] Skipping install, Ansible already installed.")

# ----------------------------
# 2. Prepare directories
# ----------------------------
ansible_dir = "/root/.ansible"
os.makedirs(ansible_dir, exist_ok=True)

# ----------------------------
# Helper: hash + copy if different
# ----------------------------
def file_hash(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def copy_if_different(src, dst, label):
    src_hash = file_hash(src)
    dst_hash = file_hash(dst)

    if dst_hash is None:
        shutil.copy2(src, dst)
        print(f"[+] {label} copied → {dst} (file did not exist)")
    elif src_hash != dst_hash:
        shutil.copy2(src, dst)
        print(f"[+] {label} updated → {dst} (content changed)")
    else:
        print(f"[i] {label} already up-to-date, skipping copy")

# ----------------------------
# 3. Copy Files (Safe + Idempotent)
# ----------------------------
base_repo_path = "/root/openShift_Cluster_Config/service_Node_Config/svc-1/config_Files/ansible"

# Copy ansible.cfg
repo_cfg = os.path.join(base_repo_path, "ansible.cfg")
dest_cfg = "/root/.ansible.cfg"

if os.path.exists(repo_cfg):
    copy_if_different(repo_cfg, dest_cfg, "ansible.cfg")
else:
    print(f"❌ Error: Source config not found at {repo_cfg}")

# Copy inventory
repo_hosts = os.path.join(base_repo_path, "hosts")
dest_hosts = os.path.join(ansible_dir, "hosts")

if os.path.exists(repo_hosts):
    copy_if_different(repo_hosts, dest_hosts, "Hosts")
else:
    if not os.path.exists(dest_hosts):
        print("[*] No hosts file found in repo, creating default")
        with open(dest_hosts, "w") as f:
            f.write("[all]\nlocalhost ansible_connection=local\n")
    else:
        print("[i] Default hosts already exists, skipping creation")

# ----------------------------
# 4. Verify Ansible
# ----------------------------
print("\n[*] Verifying installation...")

ver = run("ansible --version", check=False)

if ver.returncode != 0:
    print("❌ Ansible command not found after installation!")
    sys.exit(1)

first_line = ver.stdout.splitlines()[0].strip()
print(f"[i] Installed Ansible version: {first_line}")

result = run("ansible localhost -m ping", check=False)

if result.returncode == 0:
    print("[+] ✅ Ansible is fully operational.")
else:
    print("[-] ❌ Ping test failed. Check your local repo or python environment.")
    sys.exit(1)

print("\n🎉 Setup Complete!")
