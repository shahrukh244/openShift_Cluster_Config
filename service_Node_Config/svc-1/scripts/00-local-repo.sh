#!/bin/bash

set -e

run_command() {
    local cmd="$1"
    echo "Running: $cmd"
    eval "$cmd"
}

# Ensure script runs as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo or as root."
    exit 1
fi

# 1. Mount the ISO
echo "--- Mounting Media ---"
run_command "mkdir -p /tmp/redhat_iso"
run_command "mount /dev/sr0 /tmp/redhat_iso"

# 2. Copy the RPM data
echo "--- Copying Repositories to Local Storage ---"
run_command "mkdir -p /mnt/redhat_rpm"
run_command "cp -rf /tmp/redhat_iso/BaseOS /tmp/redhat_iso/AppStream /mnt/redhat_rpm/"

# 3. Cleanup Mount Point
echo "--- Cleaning Up ---"
run_command "umount /tmp/redhat_iso"
run_command "rm -rf /tmp/redhat_iso"

# 4. Create Local Repository Configuration
echo "--- Writing local.repo file ---"

cat > /etc/yum.repos.d/local.repo <<EOF
[AppStream]
name=AppStream
baseurl=file:///mnt/redhat_rpm/AppStream
enabled=1
gpgcheck=0

[BaseOS]
name=BaseOS
baseurl=file:///mnt/redhat_rpm/BaseOS
enabled=1
gpgcheck=0
EOF

# 5. Install EPEL
echo "--- Installing EPEL Repository ---"
run_command "yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm"

# 6. Remove unused EPEL repo files (cleanup)
echo "--- Cleaning unused EPEL repo files ---"
cd /etc/yum.repos.d

rm -f epel-testing.repo \
      epel-modular.repo \
      epel-testing-modular.repo

# 7. Manually add CRB repo (disabled by default)
echo "--- Adding CodeReady Builder repo (manual) ---"

cat > /etc/yum.repos.d/codeready.repo <<EOF
[codeready-builder]
name=CodeReady Builder
baseurl=https://cdn.redhat.com/content/dist/rhel8/8/x86_64/codeready-builder/os/
enabled=0
gpgcheck=0
EOF

# 8. Disable subscription-manager plugin (silence warnings)
echo "--- Disabling subscription-manager plugin ---"
sed -i 's/enabled=1/enabled=0/' /etc/yum/pluginconf.d/subscription-manager.conf || true

# 9. Refresh YUM and Show Repos
echo "--- Refreshing Repolist ---"
run_command "yum clean all"
run_command "yum repolist"

# 10. Install Test Package
echo "--- Installing Git ---"
run_command "yum install -y git"

echo
echo "[+] Process Complete."
echo "[+] Local BaseOS/AppStream active."
echo "[+] EPEL active (stable only)."
echo "[+] CRB added but disabled (enable only if needed)."
