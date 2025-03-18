#!/usr/bin/env python3
import socket
import argparse
import random
import time
import threading
import queue
import sys
import numpy as np
import matplotlib.pyplot as plt
from time import localtime, strftime

# maximum port number
MAX_PORT_NUM = 65535

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='UDP Proxy with Network Simulation')
    parser.add_argument('--listen-ip', default='0.0.0.0',
                        help='IP address to listen on for client connections')
    parser.add_argument('--listen-port', type=int, default=5001,
                        help='Port to listen on for client connections')
    parser.add_argument('--server-ip', default='127.0.0.1',
                        help='IP address of the actual server')
    parser.add_argument('--server-port', type=int, default=5000,
                        help='Port of the actual server')
    parser.add_argument('--client-drop', type=float, default=0.0,
                        help='Drop chance (0%% - 100%%) for packets from the client')
    parser.add_argument('--server-drop', type=float, default=0.0,
                        help='Drop chance (0%% - 100%%) for packets from the server')
    parser.add_argument('--client-delay', type=float, default=0.0,
                        help='Delay chance (0%% - 100%%) for packets from the client')
    parser.add_argument('--server-delay', type=float, default=0.0,
                        help='Delay chance (0%% - 100%%) for packets from the server')
    parser.add_argument('--client-delay-time', type=str, default='100',
                        help='Delay time in milliseconds for client packets (fixed or range as min-max)')
    parser.add_argument('--server-delay-time', type=str, default='100',
                        help='Delay time in milliseconds for server packets (fixed or range as min-max)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()

    # Error checking and handling

    # if listen port is not numeric
    if(str(args.listen_port).isnumeric() == False):

        # show error message and exit
        usage(1, "The listen port number must be a positive integer.")

    # else if port number exceeds maximum valid port number
    elif(int(args.listen_port) > MAX_PORT_NUM):

        # show error message and exit
        usage(1, "Valid listen port number range is between 0 to 65535.")

    # if server port is not numeric
    if(str(args.server_port).isnumeric() == False):

        # show error message and exit
        usage(1, "The server port number must be a positive integer.")

    # else if port number exceeds maximum valid port number
    elif(int(args.server_port) > MAX_PORT_NUM):

        # show error message and exit
        usage(1, "Valid server port number range is between 0 to 65535.")

    # if client drop is a negative number
    if(int(args.client_drop) < 0):

        # show error message and exit
        usage(1, "The client drop rate cannot be negative.")

    # if server drop is a negative number
    if(int(args.server_drop) < 0):

        # show error message and exit
        usage(1, "The server drop rate cannot be negative.")

    # if client delay is a negative number
    if(int(args.client_delay) < 0):

        # show error message and exit
        usage(1, "The client delay rate cannot be negative.")

    # if server delay is a negative number
    if(int(args.server_delay) < 0):

        # show error message and exit
        usage(1, "The server delay rate cannot be negative.")
    
    # Convert percentages to probabilities
    args.client_drop /= 100.0
    args.server_drop /= 100.0
    args.client_delay /= 100.0
    args.server_delay /= 100.0
    
    # Parse delay time ranges
    args.client_delay_time_range = parse_delay_time(args.client_delay_time)
    args.server_delay_time_range = parse_delay_time(args.server_delay_time)
    
    return args

def usage(exit_code, exit_message):

    # if error message exists
    if(exit_message):

        # print error message
        print(exit_message)
    
    # exit the program using the exit_code
    sys.exit(exit_code)

def parse_delay_time(delay_time_str):
    """Parse delay time string into a tuple of (min, max) delays in seconds."""
    if '-' in delay_time_str:
        min_str, max_str = delay_time_str.split('-')
        return (float(min_str) / 1000.0, float(max_str) / 1000.0)
    else:
        delay_sec = float(delay_time_str) / 1000.0
        return (delay_sec, delay_sec)

def parse_packet(packet_data):
    """Parse a packet according to our protocol format."""
    try:
        parts = packet_data.decode().split('|', 2)
        if len(parts) < 3:
            return None, None, None
        return int(parts[0]), parts[1], parts[2]
    except:
        return None, None, None

def should_drop_packet(drop_probability):
    """Determine if a packet should be dropped based on probability."""
    return random.random() < drop_probability

def should_delay_packet(delay_probability):
    """Determine if a packet should be delayed based on probability."""
    return random.random() < delay_probability

def get_random_delay(delay_range):
    """Get a random delay time within the specified range."""
    min_delay, max_delay = delay_range
    if min_delay == max_delay:
        return min_delay
    return random.uniform(min_delay, max_delay)

def log(verbose, message, force=False):
    """Log a message if verbose logging is enabled or forced."""
    if verbose or force:
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

def main():
    args = parse_arguments()
    
    # Create UDP socket for the proxy
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxy_socket.bind((args.listen_ip, args.listen_port))
    
    # Server address
    server_addr = (args.server_ip, args.server_port)
    
    # Track the latest client address
    latest_client = None
    
    # Create a queue for delayed packets
    delayed_packets = queue.Queue()
    
    # Metrics
    metrics = {
        'client_to_server_packets': 0,
        'server_to_client_packets': 0,
        'client_to_server_dropped': 0,
        'server_to_client_dropped': 0,
        'client_to_server_delayed': 0,
        'server_to_client_delayed': 0,
        'total_packets': 0
    }

    # Delay Array
    delayTotal = []
    delayClient = []
    delayServer = []

    # Delay starts from 0 ms latency
    delayTotal.append(0)
    
    print("\n" + "="*50)
    print("UDP PROXY WITH NETWORK SIMULATION")
    print("="*50)
    print(f"STATUS: Running")
    print(f"LISTENING: {args.listen_ip}:{args.listen_port}")
    print(f"FORWARDING TO: {args.server_ip}:{args.server_port}")
    print("\nNETWORK SIMULATION SETTINGS:")
    print(f"  Client→Server:")
    print(f"    - Drop chance: {args.client_drop*100:.1f}%")
    print(f"    - Delay chance: {args.client_delay*100:.1f}%")
    print(f"    - Delay time: {args.client_delay_time_range[0]*1000:.0f}-{args.client_delay_time_range[1]*1000:.0f}ms")
    print(f"  Server→Client:")
    print(f"    - Drop chance: {args.server_drop*100:.1f}%")
    print(f"    - Delay chance: {args.server_delay*100:.1f}%")
    print(f"    - Delay time: {args.server_delay_time_range[0]*1000:.0f}-{args.server_delay_time_range[1]*1000:.0f}ms")
    print("="*50)
    
    # Function to process delayed packets
    def process_delayed_packets():
        while True:
            try:
                # Get the next delayed packet from the queue
                # Format: (send_time, socket, target_addr, data)
                send_time, sock, addr, data = delayed_packets.get()
                
                # Calculate how much longer to wait
                now = time.time()
                wait_time = max(0, send_time - now)
                
                if wait_time > 0:
                    time.sleep(wait_time)
                
                # Try to parse the packet for logging
                seq_num, msg_type, _ = parse_packet(data)
                packet_type = f"seq={seq_num}, type={msg_type}" if seq_num is not None else "unparseable"
                
                # Send the packet
                sock.sendto(data, addr)
                log(args.verbose, f"  DELIVERED delayed packet ({packet_type}) to {addr}", force=True)
                
                # Mark the task as done
                delayed_packets.task_done()
            except Exception as e:
                print(f"Error in delayed packet handler: {e}")
    
    # Start the delayed packet thread
    delay_thread = threading.Thread(target=process_delayed_packets, daemon=True)
    delay_thread.start()
    
    print("Proxy ready to receive packets...")
    
    try:
        while True:
            # Receive data from either client or server
            data, addr = proxy_socket.recvfrom(2048)
            metrics['total_packets'] += 1
            
            # Try to parse the packet
            seq_num, msg_type, payload = parse_packet(data)
            
            # Check if packet is from server or client
            if addr[0] == args.server_ip and addr[1] == args.server_port:
                # Packet from server to client (ACK)
                metrics['server_to_client_packets'] += 1
                
                # Detailed packet logging
                packet_info = f"SERVER → CLIENT: "
                if seq_num is not None and msg_type is not None:
                    packet_info += f"seq={seq_num}, type={msg_type}"
                    if msg_type == "ACK":
                        packet_info += f" (Acknowledgment for sequence {seq_num})"
                    elif msg_type == "DATA":
                        packet_info += f", payload_size={len(payload or '')}"
                else:
                    packet_info += f"[Unparseable packet: {data[:20]}...]"
                
                log(args.verbose, packet_info, force=True)
                
                if latest_client:
                    # Check if we should drop this packet
                    if should_drop_packet(args.server_drop):
                        metrics['server_to_client_dropped'] += 1
                        log(args.verbose, f"  ACTION: DROPPED packet to client (probability: {args.server_drop*100:.1f}%)", force=True)
                    elif should_delay_packet(args.server_delay):
                        # Calculate when to send the packet
                        delay = get_random_delay(args.server_delay_time_range)
                        send_time = time.time() + delay
                        
                        # Queue the packet for delayed sending
                        delayed_packets.put((send_time, proxy_socket, latest_client, data))
                        metrics['server_to_client_delayed'] += 1
                        log(args.verbose, f"  ACTION: DELAYED packet to client by {delay*1000:.1f}ms", force=True)
                    
                        # Add delay time to server delay array
                        delayServer.append(delay)
                    else:
                        # Forward to the client immediately
                        log(args.verbose, f"  ACTION: FORWARDED to client: {latest_client}", force=True)
                        proxy_socket.sendto(data, latest_client)
                else:
                    print(f"  ERROR: No client to forward to. Packet dropped.")
            else:
                # Packet from client to server (DATA)
                metrics['client_to_server_packets'] += 1
                
                # Detailed packet logging
                packet_info = f"CLIENT → SERVER: "
                if seq_num is not None and msg_type is not None:
                    packet_info += f"seq={seq_num}, type={msg_type}"
                    if msg_type == "DATA":
                        packet_info += f", message=\"{payload[:50]}\"" + ("..." if len(payload) > 50 else "")
                else:
                    packet_info += f"[Unparseable packet: {data[:20]}...]"
                
                log(args.verbose, packet_info, force=True)
                
                # Update latest client
                latest_client = addr
                log(args.verbose, f"  Client address updated: {latest_client}")
                
                # Check if we should drop this packet
                if should_drop_packet(args.client_drop):
                    metrics['client_to_server_dropped'] += 1
                    log(args.verbose, f"  ACTION: DROPPED packet to server (probability: {args.client_drop*100:.1f}%)", force=True)
                elif should_delay_packet(args.client_delay):
                    # Calculate when to send the packet
                    delay = get_random_delay(args.client_delay_time_range)
                    send_time = time.time() + delay
                    
                    # Queue the packet for delayed sending
                    delayed_packets.put((send_time, proxy_socket, server_addr, data))
                    metrics['client_to_server_delayed'] += 1
                    log(args.verbose, f"  ACTION: DELAYED packet to server by {delay*1000:.1f}ms", force=True)
                
                    # Add delay time to client delay array
                    delayClient.append(delay)
                else:
                    # Forward to server immediately
                    log(args.verbose, f"  ACTION: FORWARDED to server: {server_addr}", force=True)
                    proxy_socket.sendto(data, server_addr)
            
            # Print metrics every 10 packets
            if metrics['total_packets'] % 10 == 0:
                print("\n" + "="*50)
                print("PROXY METRICS SUMMARY:")
                print("="*50)
                print(f"Total packets handled: {metrics['total_packets']}")
                
                # Client to Server metrics
                c2s_total = metrics['client_to_server_packets']
                c2s_drop_pct = (metrics['client_to_server_dropped'] / max(1, c2s_total)) * 100
                c2s_delay_pct = (metrics['client_to_server_delayed'] / max(1, c2s_total)) * 100
                c2s_forward_pct = 100 - c2s_drop_pct - c2s_delay_pct
                
                print(f"\nClient→Server: {c2s_total} packets")
                print(f"  - Forwarded: {c2s_total - metrics['client_to_server_dropped'] - metrics['client_to_server_delayed']} ({c2s_forward_pct:.1f}%)")
                print(f"  - Dropped:   {metrics['client_to_server_dropped']} ({c2s_drop_pct:.1f}%)")
                print(f"  - Delayed:   {metrics['client_to_server_delayed']} ({c2s_delay_pct:.1f}%)")
                
                # Server to Client metrics
                s2c_total = metrics['server_to_client_packets']
                s2c_drop_pct = (metrics['server_to_client_dropped'] / max(1, s2c_total)) * 100
                s2c_delay_pct = (metrics['server_to_client_delayed'] / max(1, s2c_total)) * 100
                s2c_forward_pct = 100 - s2c_drop_pct - s2c_delay_pct
                
                print(f"\nServer→Client: {s2c_total} packets")
                print(f"  - Forwarded: {s2c_total - metrics['server_to_client_dropped'] - metrics['server_to_client_delayed']} ({s2c_forward_pct:.1f}%)")
                print(f"  - Dropped:   {metrics['server_to_client_dropped']} ({s2c_drop_pct:.1f}%)")
                print(f"  - Delayed:   {metrics['server_to_client_delayed']} ({s2c_delay_pct:.1f}%)")
                
                print("="*50)

                # Add total delay time to delay total
                delayTotal.append(sum(delayClient) + sum(delayServer))

                # Empty delay arrays
                delayClient.clear()
                delayServer.clear()
                
    except KeyboardInterrupt:
        print("\nProxy shutting down gracefully...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proxy_socket.close()
        print("Proxy socket closed.")
        
        # Draw latency graph and save the file
        y = np.array(delayTotal) * 1000
        plt.plot(y)
        plt.xlabel("Every 10 Packets")
        plt.ylabel("Latency in ms")
        plt.title("Proxy Latency with Delay Configuration Graph")
        plt.savefig("graphs/Proxy Graph - " + strftime("%Y-%m-%d %H:%M:%S", localtime()))

if __name__ == "__main__":
    main()
