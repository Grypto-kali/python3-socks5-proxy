# SOCKS5 Proxy Server with Authentication

This is a simple implementation of a SOCKS5 proxy server in Python. The server supports username and password authentication.

## Features

- Supports SOCKS5 protocol
- Requires username and password authentication
- Configurable port

## Requirements

- Python 3.x

##  Security Warning

**All traffic through this proxy is unencrypted (plaintext).** This means:

- Passwords and sensitive data are visible to anyone monitoring the network
- The connection is vulnerable to man-in-the-middle (MITM) attacks
- This proxy should **not** be used on untrusted or public networks

For encrypted traffic, consider tunneling through SSH or using a VPN instead.

## Configuration

You can set the username, password, and port directly in the script:

From

```python
USERNAME = b"user"
PASSWORD = b"pass"
PORT = 1080
```

To

```python
USERNAME = b"sillygoose"
PASSWORD = b"tryhackmelol"
PORT = 1836
```
