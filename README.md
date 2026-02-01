
# Set HostName

hostnamectl set-hostname svc.lab.ocp.lan.
exec bash



# Config Local-Repo

lsblk

mkdir /tmp/redhat_iso
mount /dev/sr0 /tmp/redhat_iso/

mkdir /mnt/redhat_rpm
cp -rf /tmp/redhat_iso/BaseOS/ /tmp/redhat_iso/AppStream/ /mnt/redhat_rpm/

umount /tmp/redhat_iso
rm -rf /tmp/redhat_iso

# Local YUM
sudo bash -c 'cat > /etc/yum.repos.d/local.repo <<EOF
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
EOF'

yum repolist


yum install -y git wget

git clone https://github.com/shahrukh244/openShift_Cluster_Config.git




# Disable Swap
swapon --show
swapoff -a
sed -i '/swap/d' /etc/fstab
swapon --show



# IP Forwarding
cat /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-ipforward.conf
sysctl --system





# Install DNS

dnf install -y bind bind-utils

cp -rf ~/openShift_Cluster_Config/service_Node/config_Files/named/named.conf /etc/named.conf

chown root:named /etc/named.conf
chmod 640 /etc/named.conf

cp -rf ~/openShift_Cluster_Config/service_Node/config_Files/named/zones/ocp.lan.zone /var/named/ocp.lan.zone

cp -rf ~/openShift_Cluster_Config/service_Node/config_Files/named/zones/10.0.0.rev /var/named/10.0.0.rev

chown root:named /var/named/ocp.lan.zone
chown root:named /var/named/10.0.0.rev

chmod 640 /var/named/ocp.lan.zone
chmod 640 /var/named/10.0.0.rev

named-checkconf -z /etc/named.conf
named-checkzone ocp.lan /var/named/ocp.lan.zone
named-checkzone 0.0.10.in-addr.arpa /var/named/10.0.0.rev

firewall-cmd --add-port=53/udp --zone=internal --permanent
firewall-cmd --add-port=53/tcp --zone=internal --permanent
firewall-cmd --reload

systemctl enable named
systemctl start named
systemctl status named


dig @10.0.0.1 api.ocp.lan
dig @10.0.0.1 ocp-cp-1.ocp.lan
dig @10.0.0.1 -x 10.0.0.211





# Install DHCP

dnf install -y dhcp-server

cp -rf ~/openShift_Cluster_Config/service_Node/config_Files/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf

chown root:dhcpd /etc/dhcp/dhcpd.conf
chmod 640 /etc/dhcp/dhcpd.conf

cat > /etc/sysconfig/dhcpd << 'EOF'
# Bind DHCP server to OpenShift private network interface
DHCPDARGS=ens192
EOF

firewall-cmd --add-service=dhcp --zone=internal --permanent
firewall-cmd --reload

systemctl enable dhcpd
systemctl start dhcpd
systemctl status dhcpd

journalctl -u dhcpd -n 20 --no-pager




# Install PXT (TFTP)

dnf install -y tftp-server syslinux

systemctl enable tftp.socket
systemctl start tftp.socket

mkdir -p /var/lib/tftpboot/pxelinux.cfg
cp /usr/share/syslinux/pxelinux.0 /var/lib/tftpboot/
cp /usr/share/syslinux/menu.c32 /var/lib/tftpboot/


cp -rf ~/openShift_Cluster_Config/service_Node/config_Files/pxe/default /var/lib/tftpboot/pxelinux.cfg/default

cp -rf ~/openShift_Cluster_Config/service_Node/config_Files/pxe/grub.cfg /var/lib/tftpboot/grub.cfg

chmod 644 /var/lib/tftpboot/pxelinux.cfg/default
chmod 644 /var/lib/tftpboot/grub.cfg




# Install HTTP

dnf install -y httpd


wget https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.20/latest/rhcos-live-iso.x86_64.iso

wget https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.20/latest/rhcos-live-kernel.x86_64

wget https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.20/latest/rhcos-live-initramfs.x86_64.img


mkdir -p /var/www/html/rhcos
mv ~/rhcos-live-iso.x86_64.iso /var/www/html/rhcos/rhcos-live.x86_64.iso


mkdir -p /var/lib/tftpboot/rhcos
mv ~/rhcos-live-kernel.x86_64 /var/lib/tftpboot/rhcos/vmlinuz

mv ~/rhcos-live-initramfs.x86_64.img /var/lib/tftpboot/rhcos/initramfs.img


mkdir -p /var/www/html/ignition
chown -R apache:apache /var/www/html
chmod -R 755 /var/www/html


restorecon -Rv /var/www/html
setsebool -P httpd_read_user_content 1

systemctl restart httpd
systemctl enable --now httpd






haproxy \

chrony \
wget podman









