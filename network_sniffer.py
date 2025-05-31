from scapy.all import sniff, IP, TCP, UDP, Ether
import datetime
import argparse
import signal
import sys

packet_count = 0  # Variable to count packets captured

def packet_callback(packet):
    global packet_count
    packet_count += 1
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if Ether in packet:
        eth_src = packet[Ether].src
        eth_dst = packet[Ether].dst
        print(f"[{timestamp}] Ether Packet: {eth_src} -> {eth_dst}")

    if IP in packet:
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        print(f"[{timestamp}] IP Packet: {ip_src} -> {ip_dst}")

    if TCP in packet:
        tcp_src_port = packet[TCP].sport
        tcp_dst_port = packet[TCP].dport
        print(f"[{timestamp}] TCP Packet: {ip_src}:{tcp_src_port} -> {ip_dst}:{tcp_dst_port}")

    if UDP in packet:
        udp_src_port = packet[UDP].sport
        udp_dst_port = packet[UDP].dport
        print(f"[{timestamp}] UDP Packet: {ip_src}:{udp_src_port} -> {ip_dst}:{udp_dst_port}")

def signal_handler(sig, frame):
    print(f"\nStopping sniffer after capturing {packet_count} packets.")
    sys.exit(0)

def main(protocol):
    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    filter_str = ""
    if protocol == "tcp":
        filter_str = "tcp"
    elif protocol == "udp":
        filter_str = "udp"
    else:
        filter_str = "ip"  # Default to IP for both TCP and UDP
    
    print(f"Starting network sniffer for protocol: {protocol.upper()}")
    print("Press Ctrl + C to stop the sniffer.")
    
    # Sniff packets, with a callback to process them
    sniff(prn=packet_callback, filter=filter_str, store=0)  # Adjust filter as required

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Network Sniffer using Scapy')
    parser.add_argument('protocol', type=str, choices=['all', 'tcp', 'udp'],
                        help='Protocol to capture: "all", "tcp", or "udp"')
    
    args = parser.parse_args()
    
    main(args.protocol)
