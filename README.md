# Reliable UDP Communication Protocol

## Overview

This project implements a reliable communication protocol over UDP, consisting of three main components:
- **Client**: Sends messages and handles acknowledgments
- **Server**: Receives messages and sends acknowledgments
- **Proxy Server**: Simulates unreliable network conditions with packet loss and delays

This system demonstrates how reliable communication can be achieved over an unreliable medium (UDP) through the implementation of acknowledgments, timeouts, and retransmissions.

## Project Structure

```
reliable-udp/
├── src/
│   ├── client.py       # Client implementation
│   ├── server.py       # Server implementation
│   ├── proxy.py        # Proxy server implementation
│   └── protocol.py     # Shared protocol definitions
├── tests/
│   ├── test_basic.py   # Basic functionality tests
│   └── test_config.py  # Configuration tests
├── docs/
│   └── report.md       # Test report and analysis
├── README.md           # This file
└── requirements.txt    # Dependencies
```

## Features

- Reliable message transmission over UDP
- Configurable retry mechanism with timeouts
- Proxy server with adjustable packet loss and delay simulation
- Statistical tracking for performance analysis
- Automatic graph generation for visualization of network metrics
- Dynamic configuration of proxy parameters (for bonus marks)

## Requirements

- Python 3.8 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  - matplotlib (for graph generation)
  - argparse (for command-line argument parsing)
  - socket (included in standard library)
  - select (included in standard library)
  - random (included in standard library)
  - time (included in standard library)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/reliable-udp.git
   cd reliable-udp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Server

```bash
python src/server.py --listen-ip 0.0.0.0 --listen-port 5000
```

### Running the Client

```bash
python src/client.py --target-ip 192.168.1.10 --target-port 5000 --timeout 2
```

### Running the Proxy Server

```bash
python src/proxy.py --listen-ip 0.0.0.0 --listen-port 4000 --target-ip 192.168.1.10 --target-port 5000 --client-drop 10 --server-drop 5 --client-delay 20 --server-delay 15 --client-delay-time 100 --server-delay-time 200
```

## Protocol Design

The protocol implements the following features for reliable communication:

1. **Message Format**:
   - Sequence number (for ordering and duplicate detection)
   - Message length
   - Message data
   - Checksum (for data integrity)

2. **Reliability Mechanisms**:
   - Acknowledgment (ACK) for received messages
   - Timeouts for retransmission of lost messages
   - Sequence numbers to handle duplicates and ordering

3. **Flow Control**:
   - Simple stop-and-wait mechanism

## Testing

Test your setup with various network conditions by configuring the proxy server:

1. **No Loss or Delay**:
   ```bash
   python src/proxy.py --listen-ip 0.0.0.0 --listen-port 4000 --target-ip 192.168.1.10 --target-port 5000 --client-drop 0 --server-drop 0 --client-delay 0 --server-delay 0
   ```

2. **Moderate Loss and Delay**:
   ```bash
   python src/proxy.py --listen-ip 0.0.0.0 --listen-port 4000 --target-ip 192.168.1.10 --target-port 5000 --client-drop 50 --server-drop 50 --client-delay 50 --server-delay 50 --client-delay-time 500 --server-delay-time 500
   ```

3. **Extreme Loss and Delay**:
   ```bash
   python src/proxy.py --listen-ip 0.0.0.0 --listen-port 4000 --target-ip 192.168.1.10 --target-port 5000 --client-drop 100 --server-drop 100 --client-delay 100 --server-delay 100 --client-delay-time 3000 --server-delay-time 3000
   ```

## Dynamic Configuration (Bonus Feature)

The proxy server can be dynamically configured without restarting:

1. While the proxy is running, connect to its control interface:
   ```bash
   telnet localhost 4001  # Connect to control port (default: listen-port + 1)
   ```

2. Example commands to modify proxy behavior:
   ```
   set client-drop 75     # Set client packet drop rate to 75%
   set server-delay 80    # Set server packet delay rate to 80%
   get stats              # Get current statistics
   help                   # Show available commands
   ```

## Performance Analysis

The client, server, and proxy automatically generate performance metrics and graphs showing:

1. Number of packets sent, received, retransmitted, and lost
2. Latency observed with different delay configurations
3. Success rate under various network conditions

Graphs are saved to the `graphs/` directory in PNG format with timestamps.

## Troubleshooting

- **Permission Denied**: When binding to ports below 1024, you may need elevated privileges:
  ```bash
  sudo python src/server.py --listen-ip 0.0.0.0 --listen-port 80
  ```

- **Address Already in Use**: Ensure no other application is using the specified ports:
  ```bash
  lsof -i :5000  # Check if port 5000 is in use
  ```

- **No Response**: Check that all components (client, server, proxy) are running and using the correct IP addresses and ports

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
