#!/usr/bin/env python3
import socket
import argparse
import time
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from time import localtime, strftime

# maximum port number
MAX_PORT_NUM = 65535

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Reliable UDP Client')
    parser.add_argument('--target-ip', default='127.0.0.1',
                        help='Target server IP address')
    parser.add_argument('--target-port', type=int, default=5001,
                        help='Target server port')
    parser.add_argument('--timeout', type=float, default=1.0,
                        help='Timeout in seconds before retransmission (0.0 for non-blocking)')
    
    args = parser.parse_args()

    # Error checking and handling

    # if target port is not numeric
    if(str(args.target_port).isnumeric() == False):

        # show error message and exit
        usage(1, "The target port number must be a positive integer.")

    # else if target port number exceeds maximum valid port number
    elif(int(args.target_port) > MAX_PORT_NUM):

        # show error message and exit
        usage(1, "Valid target port number range is between 0 to 65535.")

    # if timeout is a negative number
    if(int(args.timeout) < 0):

        # show error message and exit
        usage(1, "Timeout cannot be negative.")

    return args

def usage(exit_code, exit_message):

    # if error message exists
    if(exit_message):

        # print error message
        print(exit_message)
    
    # exit the program using the exit_code
    sys.exit(exit_code)

def create_packet(seq_num, message_type, payload=""):
    """Create a packet with the protocol format."""
    return f"{seq_num}|{message_type}|{payload}".encode()

def parse_packet(packet_data):
    """Parse a packet according to the protocol format."""
    try:
        parts = packet_data.decode().split('|', 2)
        if len(parts) < 3:
            return None, None, None
        return int(parts[0]), parts[1], parts[2]
    except (UnicodeDecodeError, ValueError) as e:
        print(f"Error parsing packet: {e}")
        return None, None, None

def main():
    args = parse_arguments()
    
    # Initialize metrics
    packets_sent = 0
    retransmissions = 0
    acks_received = 0
    
    # Create UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Handle socket configuration based on timeout value
    if args.timeout == 0.0:
        # If timeout is 0, use a small but reasonable timeout
        # A value of 0.0 in UDP sockets means non-blocking which requires special handling
        timeout = 0.1
        client_socket.settimeout(timeout)
        print(f"Socket timeout set to {timeout} seconds (minimum viable timeout)")
    else:
        # Normal blocking mode with timeout
        client_socket.settimeout(args.timeout)
        print(f"Socket timeout set to {args.timeout} seconds")
    
    # RTT tracking for metrics
    rtt_values = []
    
    # Start with sequence number 0
    seq_num = 0
    
    # Create graphs directory if it doesn't exist
    os.makedirs("graphs", exist_ok=True)
    
    print(f"UDP Client started. Connecting to {args.target_ip}:{args.target_port}")
    # This line is no longer needed since we already print the timeout info when setting it
    print("Type a message and press Enter to send. Type 'exit' to quit.")
    
    while True:
        # Get message from user
        try:
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
                    try:
                        data, addr = client_socket.recvfrom(1024)
                        ack_seq, msg_type, _ = parse_packet(data)
                        
                        # Check if the acknowledgment matches our sequence number
                        if msg_type == "ACK" and ack_seq == seq_num:
                            acks_received += 1
                            rtt = time.time() - packet_sent_time
                            rtt_values.append(rtt)
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
                    
                    except BlockingIOError:
                        # Handle non-blocking socket (should not happen with our configuration)
                        print("Socket is in non-blocking mode. This should not happen with our configuration.")
                        time.sleep(0.1)  # Short sleep to prevent CPU spinning
                
                except Exception as e:
                    print(f"Error during transmission: {e}")
                    break
                    
        except KeyboardInterrupt:
            print("\nClient shutting down...")
            break
    
    # Print final metrics
    print("\nClient Metrics:")
    print(f"Total packets sent: {packets_sent}")
    print(f"Retransmissions: {retransmissions}")
    print(f"ACKs received: {acks_received}")
    
    loss_rate = (packets_sent - acks_received) / max(packets_sent, 1) * 100
    print(f"Packet loss rate: {loss_rate:.2f}%")
    
    if rtt_values:
        avg_rtt = sum(rtt_values) / len(rtt_values)
        print(f"Average RTT: {avg_rtt:.6f} seconds")
    
    client_socket.close()

    # Draw graph if we have data
    if packets_sent > 0:
        # First graph: Packet statistics
        labels = ["Sent", "Received", "Retransmissions", "Lost"]
        values = [packets_sent, acks_received, retransmissions, packets_sent-acks_received]
        
        plt.figure(figsize=(10, 6))
        plt.bar(labels, values, color=['blue', 'green', 'orange', 'red'])
        plt.xlabel("Packet Type")
        plt.ylabel("Number of Packets")
        plt.title("Client Packet Communication Statistics")
        timestamp = strftime("%Y-%m-%d_%H-%M-%S", localtime())
        plt.savefig(f"graphs/client_stats_{timestamp}.png")
        plt.close()
        
        # Second graph: RTT over time if we have RTT values
        if rtt_values:
            plt.figure(figsize=(10, 6))
            plt.plot(range(1, len(rtt_values) + 1), rtt_values, marker='o')
            plt.xlabel("Packet Number")
            plt.ylabel("Round Trip Time (seconds)")
            plt.title("Round Trip Time per Packet")
            plt.grid(True)
            plt.savefig(f"graphs/client_rtt_{timestamp}.png")
            plt.close()
        
        print(f"Graphs saved to graphs/ directory")

if __name__ == "__main__":
    main()
