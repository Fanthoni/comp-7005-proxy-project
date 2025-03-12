# Reliable UDP Communication System

This project implements a reliable communication system over UDP with three components: a client, a server, and a proxy server that simulates network unreliability. The system demonstrates how to achieve reliable data transmission over an unreliable protocol by implementing acknowledgments, timeouts, and retransmissions.

## System Architecture

The system consists of three main components:

1. **Client** - Sends messages to the server and handles retransmissions when acknowledgments aren't received.
2. **Server** - Receives messages from the client and sends acknowledgments.
3. **Proxy Server** - Sits between the client and server to simulate network unreliability (packet loss and delays).

![System Architecture](images/system_architecture.png)

## Protocol

The system uses a simple protocol for communication:

- Each packet has a format: `sequence_number|message_type|payload`
- Sequence numbers are used to track message order
- Message types include DATA (from client) and ACK (from server)
- Retry mechanism with configurable timeout values

## Features

- **Reliable Communication**: Ensures message delivery despite network unreliability
- **Configurable Network Simulation**: Proxy server with adjustable drop rates and delays
- **Dynamic Configuration**: Change network conditions without restarting
- **Metrics Collection**: Track packet statistics in real-time
- **Visualization**: Generate graphs to visualize network performance

## Requirements

- Python 3.6+
- numpy
- matplotlib

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Fanthoni/comp-7005-proxy-project.git
   cd reliable-udp
   ```

2. Install required dependencies:
   ```
   pip install numpy matplotlib
   ```

3. Make sure the scripts have execution permissions:
   ```
   chmod +x server.py client.py proxy.py
   ```

## Usage

### Running the Server

```bash
python server.py [--listen-ip IP] [--listen-port PORT]
```

#### Arguments:
- `--listen-ip`: IP address to listen on (default: 0.0.0.0)
- `--listen-port`: Port to listen on (default: 5000)

### Running the Proxy

```bash
python proxy.py [--listen-ip IP] [--listen-port PORT] [--server-ip IP] [--server-port PORT] [--client-drop PERCENT] [--server-drop PERCENT] [--client-delay PERCENT] [--server-delay PERCENT] [--client-delay-time MS] [--server-delay-time MS] [--verbose]
```

#### Arguments:
- `--listen-ip`: IP address to listen on (default: 0.0.0.0)
- `--listen-port`: Port to listen on (default: 5001)
- `--server-ip`: IP address of the actual server (default: 127.0.0.1)
- `--server-port`: Port of the actual server (default: 5000)
- `--client-drop`: Drop chance (0% - 100%) for packets from the client (default: 0.0)
- `--server-drop`: Drop chance (0% - 100%) for packets from the server (default: 0.0)
- `--client-delay`: Delay chance (0% - 100%) for packets from the client (default: 0.0)
- `--server-delay`: Delay chance (0% - 100%) for packets from the server (default: 0.0)
- `--client-delay-time`: Delay time in milliseconds for client packets (fixed or range as min-max, default: 100)
- `--server-delay-time`: Delay time in milliseconds for server packets (fixed or range as min-max, default: 100)
- `--verbose`: Enable verbose logging

### Running the Client

```bash
python client.py [--target-ip IP] [--target-port PORT] [--timeout SECONDS]
```

#### Arguments:
- `--target-ip`: Target server IP address (default: 127.0.0.1)
- `--target-port`: Target server port (default: 5001)
- `--timeout`: Timeout in seconds before retransmission (default: 1.0)

## Example Setup

1. Start the server:
   ```
   python server.py --listen-port 5000
   ```

2. Start the proxy with 50% packet loss simulation:
   ```
   python proxy.py --listen-port 5001 --server-port 5000 --client-drop 50 --server-drop 50 --verbose
   ```

3. Start the client:
   ```
   python client.py --target-port 5001 --timeout 2.0
   ```

4. Type messages in the client console and observe the behavior.

## Proxy Command Interface

The proxy has a command interface for dynamic configuration. Type `help` in the proxy console to see available commands:

- `show` - Display current configuration
- `set <param> <value>` - Set a specific parameter
- `reset` - Reset all parameters to 0
- `presets` - Show available presets
- `preset <name>` - Load a specific preset
- `exit`/`quit` - Exit command interface

### Available presets:

- `perfect` - 0% drop, 0% delay
- `mild` - 10% drop, 20% delay (100ms)
- `moderate` - 25% drop, 40% delay (100-300ms)
- `severe` - 50% drop, 60% delay (200-500ms)
- `chaotic` - 70% drop, 80% delay (300-1000ms)
- `blackhole` - 100% drop, 0% delay

## Metrics and Visualization

The system automatically collects metrics and generates graphs:

- **Client**: Packet statistics (sent, received, retransmissions, lost) and RTT over time
- **Server**: Packet statistics (received, unique, duplicates)
- **Proxy**: Network simulation metrics and latency graphs

All graphs are saved in the `graphs/` directory.

## How It Works

1. The client sends a message with a sequence number to the proxy
2. The proxy may drop, delay, or forward the message to the server
3. The server receives the message and sends an acknowledgment
4. The proxy may drop, delay, or forward the acknowledgment to the client
5. If the client doesn't receive an acknowledgment within the timeout period, it retransmits the message

## Testing Scenarios

Test the system under different network conditions:

1. **Perfect Network**: Set drop and delay chances to 0%
2. **Mild Unreliability**: Set drop chance to 10%, delay chance to 20%
3. **Severe Unreliability**: Set drop chance to 50%, delay chance to 60%
4. **Complete Failure**: Set drop chance to 100% (blackhole)

## Troubleshooting

- If packets aren't being transmitted, verify that all components are running and port numbers match
- If the client isn't receiving acknowledgments, try increasing the timeout value
- If graphs aren't being generated, ensure the `graphs/` directory exists

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request