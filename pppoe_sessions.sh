#! /bin/bash

INTERFACE=enp0s25

VXLAN_IFNAME=vxbng
VXLAN_ID=100
VXLAN_LOCAL=172.16.250.197
VXLAN_REMOTE=172.16.248.35
VXLAN_DSTPORT=4789

S_VLAN_ID=100
S_VLAN_IFNAME=$VXLAN_IFNAME.$S_VLAN_ID

NETNS_PREFIX=$VXLAN_IFNAME

start_pppoe_connection () {
    local namespace=$1
    local ifname=$2

    ip netns exec $namespace pppd pty "/usr/sbin/pppoe -I $ifname -T 80 -U -m 1412" noccp ipparam $ifname linkname $ifname noipdefault noauth default-asyncmap defaultroute hide-password updetach mtu 1492 mru 1492 noaccomp nodeflate nopcomp novj novjccomp lcp-echo-interval 40 lcp-echo-failure 3 user intel
}

create_vxlan_interface () {
    local vx_ifname=$1
    local vx_id=$2
    local vx_dev=$3
    local vx_local=$4
    local vx_remote=$5
    local vx_dstport=$6

    ip link add $vx_ifname \
        type vxlan \
        id $vx_id \
        dev $vx_dev \
        local $vx_local \
        remote $vx_remote \
        dstport $vx_dstport \
        nolearning

    ip link set $vx_ifname up
}

create_namespace () {
    local name=$1
    local ifname=$2

    ip netns add $name
    ip link set dev $ifname netns $name
    ip netns exec $name ip link set $ifname up
}

create_service_interface () {
    local ifname=$1
    local s_id=$2

    local s_ifname=$ifname.$s_id
    ip link add link $ifname $s_ifname\
        type vlan \
        proto 802.1ad \
        id $s_id

    ip link set $s_ifname up
}

create_customer_interface () {
    local ifname=$1
    local c_id=$2
    local c_ifname=$ifname.$c_id

    ip link add link $ifname $c_ifname\
        type vlan \
        proto 802.1Q \
        id $c_id

    ip link set $c_ifname up
}

delete_namespaces () {
    local namespace_prefix=$1

    local namespaces=$(ip netns show | grep $namespace_prefix | awk '{print $1}' | xargs)
    for ns in $namespaces; do
        ip netns delete $ns
    done
}

start_session () {
    local ifname=$1
    local c_id=$2
    local namespace=$3

    local c_ifname=$ifname.$c_id
    create_customer_interface $ifname $c_id
    create_namespace $namespace $c_ifname
    start_pppoe_connection $namespace $c_ifname
}

delete_interfaces () {
    local prefix=$1

    local interfaces=$(ip a | tac | grep "$prefix" | awk 'match($2, /([^@]*)(.*:.*)/, m) {printf m[1] " "}')
    for interface in $interfaces; do
        ip link delete $interface
    done
}

kill_sessions () {
    pkill -KILL /usr/sbin/pppoe > /dev/null 2>&1
    pkill -KILL pppd > /dev/null 2>&1
}

start_sessions () {
    create_vxlan_interface $VXLAN_IFNAME \
        $VXLAN_ID \
        $INTERFACE \
        $VXLAN_LOCAL \
        $VXLAN_REMOTE \
        $VXLAN_DSTPORT

    create_service_interface $VXLAN_IFNAME \
        $S_VLAN_ID

    for id in {25..100}; do
        local namespace=$NETNS_PREFIX.$S_VLAN_ID.$id
        start_session $S_VLAN_IFNAME $id $namespace
    done
}

clean_up () {
    kill_sessions
    delete_namespaces $NETNS_PREFIX
    delete_interfaces $VXLAN_IFNAME
}

while :; do
    case $1 in
        -h|-\?|--help)
            echo "help"
            exit
            ;;
        start)
            start_sessions
            ;;
        stop)
            clean_up
            ;;
        -?*)
            printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
            ;;
        *)
            break
    esac

    shift
done
