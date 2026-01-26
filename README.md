
# Set HostName

hostnamectl set-hostname svc-1.ocp.lan
bash




# Config Local-Repo

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
yum install -y git



git clone https://github.com/shahrukh244/openShift_Cluster_Config.git



# Static IP for ens160

mv /etc/NetworkManager/system-connections/ens160.nmconnection /etc/NetworkManager/system-connections/ens160.nmconnection.ORG

cp -rf openShift_Cluster_Config/service_Node/svc-1/config_Files/network-ip/ens160.nmconnection /etc/NetworkManager/system-connections/ens160.nmconnection

chmod 600 /etc/NetworkManager/system-connections/ens160.nmconnection



# Static IP for ens192

mv /etc/NetworkManager/system-connections/ens192.nmconnection /etc/NetworkManager/system-connections/ens192.nmconnection.ORG

cp -rf openShift_Cluster_Config/service_Node/svc-1/config_Files/network-ip/ens192.nmconnection /etc/NetworkManager/system-connections/ens192.nmconnection

chmod 600 /etc/NetworkManager/system-connections/ens192.nmconnection



nmcli connection modify ens192 connection.zone internal
nmcli connection modify ens160 connection.zone external

firewall-cmd --set-default-zone=internal
firewall-cmd --reload
firewall-cmd --get-active-zones

firewall-cmd --zone=external --add-masquerade --permanent
firewall-cmd --zone=internal --set-target=ACCEPT --permanent
firewall-cmd --reload

systemctl restart NetworkManager





# Install DNS

dnf install bind bind-utils -y

mv /etc/named.conf /etc/named.conf.ORG

cp -rf openShift_Cluster_Config/service_Node/svc-1/config_Files/named/named.conf /etc/named.conf

chown root:named /etc/named.conf
chmod 640 /etc/named.conf

cp -rf openShift_Cluster_Config/service_Node/svc-1/config_Files/named/zones /etc/named

chown root:named /etc/named/zones/db.ocp.lan
chown root:named /etc/named/zones/db.reverse

chmod 640 /etc/named/zones/db.ocp.lan
chmod 640 /etc/named/zones/db.reverse


firewall-cmd --add-port=53/udp --zone=internal --permanent
firewall-cmd --add-port=53/tcp --zone=internal --permanent
firewall-cmd --reload

systemctl enable named
systemctl start named
systemctl status named





# Install DHCP

dnf install dhcp-server -y

mv /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.ORG

cp -rf openShift_Cluster_Config/service_Node/svc-1/config_Files/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf

chown root:dhcpd /etc/dhcp/dhcpd.conf
chmod 640 /etc/dhcp/dhcpd.conf

firewall-cmd --add-service=dhcp --zone=internal --permanent
firewall-cmd --reload

systemctl enable dhcpd
systemctl start dhcpd
systemctl status dhcpd





# Install HAProxy

dnf install haproxy -y

mv /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.ORG

cp openShift_Cluster_Config/service_Node/svc-1/config_Files/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg


firewall-cmd --add-port=6443/tcp --zone=internal --permanent
firewall-cmd --add-port=6443/tcp --zone=external --permanent
firewall-cmd --add-port=22623/tcp --zone=internal --permanent
firewall-cmd --add-service=http --zone=internal --permanent
firewall-cmd --add-service=http --zone=external --permanent
firewall-cmd --add-service=https --zone=internal --permanent
firewall-cmd --add-service=https --zone=external --permanent
firewall-cmd --add-port=9000/tcp --zone=external --permanent
firewall-cmd --reload

setsebool -P haproxy_connect_any 1
systemctl enable haproxy
systemctl start haproxy
systemctl status haproxy



