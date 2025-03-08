#!/usr/bin/env python3
import socket
import argparse
import time
import sys

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Reliable UDP Client')
    parser.add_argument('--target-ip', default='127.0.0.1',
                        help='Target server IP address')
    parser.add_argument('--target-port', type=int, default=5000,
                        help='Target server port')
    parser.add_argument('--timeout', type=float, default=0.0,
                        help='Timeout in seconds before retransmission')
    return parser.parse_args()

def create_packet(seq_num, message_type, payload=""):
    """Create a packet with the protocol format."""
    return f"{seq_num}|{message_type}|{payload}".encode()

def parse_packet(packet_data):
    """Parse a packet according to the protocol format."""
    parts = packet_data.decode().split('|', 2)
    if len(parts) < 3:
        return None, None, None
    return int(parts[0]), parts[1], parts[2]

def main():
    args = parse_arguments()
    
    # Initialize metrics
    packets_sent = 0
    retransmissions = 0
    acks_received = 0
    
    # Create UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(args.timeout)
    
    # Start with sequence number 0
    seq_num = 0
    
    print(f"UDP Client started. Connecting to {args.target_ip}:{args.target_port}")
    print("Type a message and press Enter to send. Type 'exit' to quit.")
    
    while True:
        # Get message from user
        message = input("> ")
        if message.lower() == 'exit':
            break
        
        max_retries = 5
        retry_count = 0
        packet_sent_time = None
        
        while retry_count <= max_retries:
            try:
                # Send the packet if it's the first attempt or a retry
                if retry_count == 0 or packet_sent_time is None:
                    packet = create_packet(seq_num, "DATA", message)
                    client_socket.sendto(packet, (args.target_ip, args.target_port))
                    packet_sent_time = time.time()
                    packets_sent += 1
                    print(f"Sent packet with seq_num {seq_num}")
                
                # Wait for acknowledgment
                data, addr = client_socket.recvfrom(1024)
                ack_seq, msg_type, _ = parse_packet(data)
                
                # Check if the acknowledgment matches our sequence number
                if msg_type == "ACK" and ack_seq == seq_num:
                    acks_received += 1
                    rtt = time.time() - packet_sent_time
                    print(f"Received ACK for seq_num {seq_num}. RTT: {rtt:.6f} seconds")
                    seq_num += 1  # Increment sequence number for next message
                    break  # Exit retry loop on successful ACK
                else:
                    print(f"Received unexpected packet. Expected ACK for {seq_num}, got {msg_type} for {ack_seq}")
            
            except socket.timeout:
                retry_count += 1
                retransmissions += 1
                print(f"Timeout. Retrying {retry_count}/{max_retries}...")
                
                if retry_count > max_retries:
                    print(f"Failed to send message after {max_retries} retries.")
                    break
    
    # Print final metrics
    print("\nClient Metrics:")
    print(f"Total packets sent: {packets_sent}")
    print(f"Retransmissions: {retransmissions}")
    print(f"ACKs received: {acks_received}")
    print(f"Packet loss rate: {(retransmissions/(packets_sent+0.0001))*100:.2f}%")
    
    client_socket.close()

if __name__ == "__main__":
    main()