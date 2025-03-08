#!/usr/bin/env python3
import socket
import argparse
import time
import threading

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Reliable UDP Server')
    parser.add_argument('--listen-ip', default='0.0.0.0',
                        help='IP address to listen on')
    parser.add_argument('--listen-port', type=int, default=5000,
                        help='Port to listen on')
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

def input_listener(exit_event):
    """Wait for user input and set exit_event when 'exit' is typed."""
    while True:
        user_input = input()
        if user_input.strip().lower() == "exit":
            exit_event.set()
            break

def main():
    args = parse_arguments()
    
    # Initialize metrics
    packets_received = 0
    unique_packets_received = 0
    duplicate_packets = 0
    acks_sent = 0

    # Create UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((args.listen_ip, args.listen_port))
    
    # Track last sequence number seen from each client
    client_seq_nums = {}
    
    print(f"UDP Server started. Listening on {args.listen_ip}:{args.listen_port}")
    
    # Create an event to signal exit
    exit_event = threading.Event()
    # Start a thread to listen for user input ("exit")
    input_thread = threading.Thread(target=input_listener, args=(exit_event,), daemon=True)
    input_thread.start()
    
    try:
        while not exit_event.is_set():
            # Set a short timeout for recvfrom to periodically check the exit_event.
            server_socket.settimeout(1.0)
            try:
                data, client_addr = server_socket.recvfrom(1024)
            except socket.timeout:
                continue  # Go back and check for exit_event
            packets_received += 1
            
            # Parse the packet
            seq_num, msg_type, payload = parse_packet(data)
            if seq_num is None:
                print("Received malformed packet.")
                continue
            
            client_key = f"{client_addr[0]}:{client_addr[1]}"
            
            # Check if this is a new packet from this client
            is_new_packet = False
            if client_key not in client_seq_nums:
                client_seq_nums[client_key] = seq_num - 1
                is_new_packet = True
            elif seq_num > client_seq_nums[client_key]:
                is_new_packet = True
            
            # Update metrics based on whether this is a new or duplicate packet
            if is_new_packet:
                unique_packets_received += 1
                client_seq_nums[client_key] = seq_num
                print(f"[{time.strftime('%H:%M:%S')}] Received new packet from {client_key}:")
                print(f"  Sequence: {seq_num}, Type: {msg_type}, Message: {payload}")
            else:
                duplicate_packets += 1
                print(f"[{time.strftime('%H:%M:%S')}] Received duplicate packet from {client_key}:")
                print(f"  Sequence: {seq_num}, Type: {msg_type} (already processed)")
            
            # Send ACK regardless of whether it's a new packet or duplicate
            ack_packet = create_packet(seq_num, "ACK")
            server_socket.sendto(ack_packet, client_addr)
            acks_sent += 1
            
            # Print periodic metrics (every 10 packets)
            if packets_received % 10 == 0:
                print("\nServer Metrics:")
                print(f"Total packets received: {packets_received}")
                print(f"Unique packets: {unique_packets_received}")
                print(f"Duplicate packets: {duplicate_packets}")
                print(f"ACKs sent: {acks_sent}")
                print(f"Duplication rate: {(duplicate_packets/packets_received)*100:.2f}%\n")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("\nExiting server. Final Metrics:")
        print(f"Total packets received: {packets_received}")
        print(f"Unique packets: {unique_packets_received}")
        print(f"Duplicate packets: {duplicate_packets}")
        print(f"ACKs sent: {acks_sent}")
        print(f"Duplication rate: {(duplicate_packets/packets_received)*100:.2f}%")
        server_socket.close()

if __name__ == "__main__":
    main()