
# Set HostName

hostnamectl set-hostname svc.ocp.lan
bash



# Share Disk 

parted /dev/nvme0n2 --script mklabel gpt
parted /dev/nvme0n2 --script mkpart primary xfs 0% 100%

lsblk | grep nvme0n2
mkfs.xfs /dev/nvme0n2p1

mkdir /share
mount /dev/nvme0n2p1 /share
blkid /dev/nvme0n2p1

echo 'UUID=af9ea414-9df6-4518-bf82-86544069652a /share xfs defaults 0 0' >> /etc/fstab
grep /share /etc/fstab




# Config Local-Repo

mkdir /tmp/redhat_iso
mount /dev/sr0 /tmp/redhat_iso/

mkdir /share/redhat_rpm
cp -rf /tmp/redhat_iso/BaseOS/ /tmp/redhat_iso/AppStream/ /share/redhat_rpm/

umount /tmp/redhat_iso
rm -rf /tmp/redhat_iso

# Local YUM
sudo bash -c 'cat > /etc/yum.repos.d/local.repo <<EOF
[AppStream]
name=AppStream
baseurl=file:///share/redhat_rpm/AppStream
enabled=1
gpgcheck=0

[BaseOS]
name=BaseOS
baseurl=file:///share/redhat_rpm/BaseOS
enabled=1
gpgcheck=0
EOF'

yum repolist
yum install -y git wget



git clone https://github.com/shahrukh244/openShift_Cluster_Config.git



# Static IP for ens160

mv /etc/NetworkManager/system-connections/ens160.nmconnection /etc/NetworkManager/system-connections/ens160.nmconnection.ORG

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/network-ip/ens160.nmconnection /etc/NetworkManager/system-connections/ens160.nmconnection

chmod 600 /etc/NetworkManager/system-connections/ens160.nmconnection



# Static IP for ens192

mv /etc/NetworkManager/system-connections/ens192.nmconnection /etc/NetworkManager/system-connections/ens192.nmconnection.ORG

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/network-ip/ens192.nmconnection /etc/NetworkManager/system-connections/ens192.nmconnection

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

reboot





# Install DNS

dnf install bind bind-utils -y

mv /etc/named.conf /etc/named.conf.ORG

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/named/named.conf /etc/named.conf

chown root:named /etc/named.conf
chmod 640 /etc/named.conf

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/named/zones /etc/named

chown root:named /etc/named/zones/db.ocp.lan
chown root:named /etc/named/zones/db.reverse

chmod 640 /etc/named/zones/db.ocp.lan
chmod 640 /etc/named/zones/db.reverse

named-checkconf -z /etc/named.conf
named-checkzone ocp.lan /etc/named/zones/db.ocp.lan
named-checkzone 0.0.10.in-addr.arpa /etc/named/zones/db.reverse

firewall-cmd --add-port=53/udp --zone=internal --permanent
firewall-cmd --add-port=53/tcp --zone=internal --permanent
firewall-cmd --reload

systemctl enable named
systemctl start named
systemctl status named





# Install DHCP

dnf install dhcp-server -y

mv /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.ORG

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf

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





# Install HAProxy

dnf install haproxy -y

mv /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.ORG

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg


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





dnf install httpd -y

sed -i 's/Listen 80/Listen 0.0.0.0:8080/' /etc/httpd/conf/httpd.conf

firewall-cmd --add-port=8080/tcp --zone=internal --permanent
firewall-cmd --reload

systemctl enable httpd
systemctl start httpd
systemctl status httpd







dnf install nfs-utils -y

mkdir -p /share/OpenShift/StorageClass/Delete
mkdir -p /share/OpenShift/StorageClass/Retain
chown -R nobody:nobody /share/OpenShift
chmod -R 777 /share/OpenShift

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/nfs/exports /etc/exports

chmod 644 /etc/exports

exportfs -rv

firewall-cmd --zone=internal --add-service mountd --permanent
firewall-cmd --zone=internal --add-service rpc-bind --permanent
firewall-cmd --zone=internal --add-service nfs --permanent
firewall-cmd --reload

systemctl enable nfs-server rpcbind
systemctl start nfs-server rpcbind nfs-mountd




timedatectl set-timezone UTC


mkdir ~/ocp-install

cp -rf /root/openShift_Cluster_Config/service_Node/config_Files/install-config.yaml ~/ocp-install

ssh-keygen

cat .ssh/id_rsa.pub

# Now past "pub key" in "sshKey:" 
vi ~/ocp-install/install-config.yaml




wget https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/4.20.0/openshift-install-linux.tar.gz

tar xzvf openshift-install-linux.tar.gz


wget https://mirror.openshift.com/pub/openshift-v4/x86_64/dependencies/rhcos/4.20/latest/rhcos-metal.x86_64.raw.gz



# For "OC" Command
wget https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/4.20.0/openshift-client-linux.tar.gz

tar -xzvf openshift-client-linux.tar.gz

cp oc /usr/local/bin/

# For "kubectl" Command

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && mv kubectl /usr/local/bin/
kubectl version --client


















