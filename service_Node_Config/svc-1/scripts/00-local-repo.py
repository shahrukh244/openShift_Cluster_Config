import subprocess
import os
import sys

def run_command(command):
    """Executes shell commands and handles failures."""
    try:
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Command failed: {e}")
        sys.exit(1)

def main():
    # 1. Mount the ISO
    print("--- Mounting Media ---")
    run_command("mkdir -p /tmp/redhat_iso")
    run_command("mount /dev/sr0 /tmp/redhat_iso")

    # 2. Copy the RPM data
    print("--- Copying Repositories to Local Storage ---")
    run_command("mkdir -p /mnt/redhat_rpm")
    # Using -rf to ensure entire directory structures are copied
    run_command("cp -rf /tmp/redhat_iso/BaseOS /tmp/redhat_iso/AppStream /mnt/redhat_rpm/")

    # 3. Cleanup Mount Point
    print("--- Cleaning Up ---")
    run_command("umount /tmp/redhat_iso")
    run_command("rm -rf /tmp/redhat_iso")

    # 4. Create Repository Configuration
    repo_content = """[AppStream]
name=AppStream
baseurl=file:///mnt/redhat_rpm/AppStream
enabled=1
gpgcheck=0

[BaseOS]
name=BaseOS
baseurl=file:///mnt/redhat_rpm/BaseOS
enabled=1
gpgcheck=0
"""
    
    print("--- Writing local.repo file ---")
    repo_path = "/etc/yum.repos.d/local.repo"
    try:
        with open(repo_path, "w") as f:
            f.write(repo_content)
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)

    # 5. Refresh YUM and Install Test Package
    print("--- Refreshing Repolist ---")
    run_command("yum clean all")
    run_command("yum repolist")

    print("--- Installing Git ---")
    run_command("yum install -y git")

if __name__ == "__main__":
    # Ensure script runs as root
    if os.geteuid() != 0:
        print("Please run this script with sudo or as root.")
        sys.exit(1)
        
    main()
    print("\n[+] Process Complete. Local repository is active and Git is installed.")
