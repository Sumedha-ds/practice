# Network Access Guide - Connect from Other Devices

## The Issue
By default, Flask only binds to `localhost` (127.0.0.1), which means it only accepts connections from the same machine. Other devices on the network cannot connect.

## The Solution
The server now binds to `0.0.0.0`, which means it accepts connections from **all network interfaces**, allowing other devices to connect.

## How to Access the Server

### 1. From the Same Machine (Local)
```
http://localhost:5000
http://127.0.0.1:5000
```

### 2. From Other Devices on the Same Network
```
http://<YOUR_LOCAL_IP>:5000
```

For example:
```
http://192.168.1.100:5000
```

## Finding Your Local IP Address

### Method 1: When Starting the Server
The server now displays your local IP when it starts:
```
============================================================
Starting API server...
============================================================
Local access:    http://localhost:5000
Network access:  http://192.168.1.100:5000
All interfaces:  http://0.0.0.0:5000
============================================================
```

### Method 2: Terminal Commands

**On Mac/Linux:**
```bash
# Option 1: Using hostname
hostname -I

# Option 2: Using ifconfig
ifconfig | grep "inet " | grep -v 127.0.0.1

# Option 3: Using ipconfig getifaddr
ipconfig getifaddr en0  # For Wi-Fi
ipconfig getifaddr en1  # For Ethernet
```

**On Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your active network adapter.

## Testing Network Access

### From Another Device:
1. Make sure both devices are on the same network (same Wi-Fi)
2. Find your server's IP address (e.g., 192.168.1.100)
3. Test the connection:

```bash
# Test health endpoint
curl http://192.168.1.100:5000/api/health

# Test from browser
Open: http://192.168.1.100:5000/api/health
```

### From Your Laptop to Access the API:
```javascript
// Instead of localhost
const BASE_URL = 'http://localhost:5000';

// Use the server's IP
const BASE_URL = 'http://192.168.1.100:5000';

// Make API calls
fetch(`${BASE_URL}/api/auth/verify-otp`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    phone_number: '9876543210',
    otp: '1234'
  })
});
```

## Firewall Configuration

If you still can't connect, check your firewall:

### Mac:
1. Go to **System Preferences** → **Security & Privacy** → **Firewall**
2. Click **Firewall Options**
3. Make sure Python is allowed or turn off firewall for testing

### Windows:
1. Go to **Windows Defender Firewall**
2. Click **Allow an app through firewall**
3. Add Python to the allowed list

### Linux:
```bash
# Allow port 5000
sudo ufw allow 5000

# Or disable firewall temporarily
sudo ufw disable
```

## Common Issues

### Issue 1: "Connection Refused"
**Cause:** Server not running or firewall blocking
**Solution:**
- Verify server is running: `curl http://localhost:5000/api/health`
- Check firewall settings
- Ensure port 5000 is not blocked

### Issue 2: "Cannot reach server"
**Cause:** Devices not on same network
**Solution:**
- Verify both devices are on same Wi-Fi network
- Check if you're using VPN (disable it)
- Try pinging the server: `ping 192.168.1.100`

### Issue 3: "Wrong IP Address"
**Cause:** Using localhost IP instead of network IP
**Solution:**
- Don't use 127.0.0.1 or localhost from another device
- Use the actual network IP (starts with 192.168.x.x or 10.x.x.x)

## Security Note

⚠️ **Important:** Running the server on `0.0.0.0` makes it accessible to anyone on your local network. 

For development, this is fine. For production:
- Use proper authentication (already implemented with tokens)
- Use HTTPS (SSL/TLS)
- Configure proper firewall rules
- Consider using a reverse proxy (nginx, Apache)
- Use environment variables for sensitive data

## Production Deployment

For production, don't use the Flask development server. Use a production WSGI server:

### Using Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### Using uWSGI:
```bash
pip install uwsgi
uwsgi --http 0.0.0.0:5000 --wsgi-file api_server.py --callable app
```

## Quick Test Script

Save this as `test_network_access.sh`:
```bash
#!/bin/bash

# Get local IP
LOCAL_IP=$(ipconfig getifaddr en0)

echo "Testing network access..."
echo "Server IP: $LOCAL_IP"
echo ""

# Test from local
echo "1. Testing from localhost..."
curl -s http://localhost:5000/api/health | head -5

echo ""
echo "2. Testing from network IP..."
curl -s http://$LOCAL_IP:5000/api/health | head -5

echo ""
echo "Share this URL with other devices:"
echo "http://$LOCAL_IP:5000"
```

## Summary

✅ **Before:** Server only accessible from `localhost`
✅ **After:** Server accessible from any device on the network

Access URLs:
- Same machine: `http://localhost:5000`
- Other devices: `http://<YOUR_IP>:5000`

The server is now ready for testing from your laptop or any other device on the same network!

