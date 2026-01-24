#!/bin/bash
set -e

run_command() {
    local cmd="$1"
    echo "Running: $cmd"
    eval "$cmd"
}

# Ensure script runs as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root."
    exit 1
fi

echo "================================================="
echo " RHEL 9.7 Local Repo Setup (OpenShift Safe Mode) "
echo "================================================="

# 1. Mount ISO and copy BaseOS/AppStream if missing
if [ ! -d /mnt/redhat_rpm/BaseOS ] || [ ! -d /mnt/redhat_rpm/AppStream ]; then
    echo "--- Mounting Install Media ---"

    if [ ! -b /dev/sr0 ]; then
        echo "[!] /dev/sr0 not available. Insert RHEL 9.7 ISO."
        exit 1
    fi

    mkdir -p /tmp/redhat_iso
    run_command "mount /dev/sr0 /tmp/redhat_iso"

    echo "--- Copying BaseOS and AppStream to /mnt/redhat_rpm ---"
    mkdir -p /mnt/redhat_rpm
    run_command "cp -rf /tmp/redhat_iso/BaseOS /tmp/redhat_iso/AppStream /mnt/redhat_rpm/"

    echo "--- Cleaning up mount ---"
    run_command "umount /tmp/redhat_iso"
    rm -rf /tmp/redhat_iso
else
    echo "[+] BaseOS and AppStream already present, skipping ISO mount"
fi

# 2. Disable ALL existing repos (safety)
echo "--- Disabling all existing repos ---"
for f in /etc/yum.repos.d/*.repo; do
    sed -i 's/^enabled=1/enabled=0/' "$f" || true
done

# 3. Create clean local.repo (overwrite intentionally)
echo "--- Writing clean local.repo ---"
cat > /etc/yum.repos.d/local.repo <<EOF
[BaseOS]
name=RHEL-9.7-BaseOS
baseurl=file:///mnt/redhat_rpm/BaseOS
enabled=1
gpgcheck=0

[AppStream]
name=RHEL-9.7-AppStream
baseurl=file:///mnt/redhat_rpm/AppStream
enabled=1
gpgcheck=0
EOF

# 4. Disable subscription-manager plugin
echo "--- Disabling subscription-manager plugin ---"
sed -i 's/^enabled=1/enabled=0/' /etc/yum/pluginconf.d/subscription-manager.conf || true

# 5. Reset DNF state completely
echo "--- Resetting DNF cache and module state ---"
run_command "dnf clean all"
run_command "rm -rf /var/cache/dnf"
run_command "dnf module reset -y '*' || true"

# 6. Rebuild metadata from local ISO
echo "--- Rebuilding DNF metadata from local repos ---"
run_command "dnf makecache"

# 7. Show active repos
echo "--- Active Repositories ---"
run_command "dnf repolist"

# 8. Install test packages (must come only from ISO)
echo "--- Installing Git (test) ---"
run_command "dnf install -y git"

echo "--- Installing Python3 (test) ---"
run_command "dnf install -y python3"

echo
echo "================================================="
echo "[+] Local BaseOS/AppStream active (RHEL 9.7 ISO)"
echo "[+] All external repos disabled"
echo "[+] Offline-safe configuration complete"
echo "[+] Ready for Ansible and OpenShift 4.16"
echo "================================================="
