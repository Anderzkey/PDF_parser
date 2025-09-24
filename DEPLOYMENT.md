# PDF Invoice Parser - Production Deployment Guide

This guide explains how to deploy the PDF Invoice Parser web service on a production virtual machine.

## 📋 Prerequisites

- Ubuntu/Debian Linux VM
- Root access (sudo privileges)
- At least 2GB RAM and 10GB disk space
- Internet connection for package installation

## 🚀 Quick Deployment

### Option 1: Automated Deployment (Recommended)

1. **Copy files to your VM:**
   ```bash
   scp -r * user@your-vm-ip:/tmp/pdf-parser/
   ```

2. **Run the deployment script:**
   ```bash
   cd /tmp/pdf-parser
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```

3. **Update server configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/pdf-parser
   # Change server_name to your domain/IP
   sudo systemctl reload nginx
   ```

### Option 2: Manual Deployment

If you prefer to deploy manually, follow these steps:

1. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv nginx
   ```

2. **Create application directory:**
   ```bash
   sudo mkdir -p /opt/pdf-parser
   sudo mkdir -p /var/log/pdf-parser
   sudo useradd --system --group --home /opt/pdf-parser --shell /bin/false www-data
   ```

3. **Copy application files:**
   ```bash
   sudo cp *.py /opt/pdf-parser/
   sudo cp requirements.txt gunicorn.conf.py index.html /opt/pdf-parser/
   sudo chown -R www-data:www-data /opt/pdf-parser
   ```

4. **Setup virtual environment:**
   ```bash
   cd /opt/pdf-parser
   sudo -u www-data python3 -m venv venv
   sudo -u www-data venv/bin/pip install -r requirements.txt
   ```

5. **Install service:**
   ```bash
   sudo cp pdf-parser.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable pdf-parser.service
   sudo systemctl start pdf-parser.service
   ```

6. **Configure nginx:**
   ```bash
   sudo cp nginx-pdf-parser.conf /etc/nginx/sites-available/pdf-parser
   sudo ln -s /etc/nginx/sites-available/pdf-parser /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## 🔧 Configuration

### Environment Variables

You can customize the service by setting environment variables in the systemd service file:

```bash
sudo systemctl edit pdf-parser.service
```

Add:
```ini
[Service]
Environment="FLASK_ENV=production"
Environment="LOG_LEVEL=INFO"
Environment="MAX_UPLOAD_SIZE=16777216"
```

### Nginx Configuration

Edit `/etc/nginx/sites-available/pdf-parser` to:
- Change `server_name` to your domain/IP
- Configure SSL certificates for HTTPS
- Adjust file upload limits if needed

### Firewall

Allow HTTP/HTTPS traffic:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📊 Monitoring

### Service Status
```bash
# Check service status
sudo systemctl status pdf-parser.service

# View real-time logs
sudo journalctl -u pdf-parser.service -f

# Check nginx status
sudo systemctl status nginx
```

### Log Files
- Application logs: `/var/log/pdf-parser/app.log`
- Error logs: `/var/log/pdf-parser/error.log`
- Access logs: `/var/log/pdf-parser/access.log`
- Nginx logs: `/var/log/nginx/pdf-parser-*.log`

### Health Check
```bash
# API health check
curl http://localhost/health

# Full API test
curl -X POST http://localhost/api/v1/parse/info
```

## 🔒 Security

### SSL Configuration

For HTTPS, obtain SSL certificates and update nginx configuration:

1. **Using Let's Encrypt:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Using custom certificates:**
   Update the nginx configuration to uncomment SSL sections and set certificate paths.

### Firewall Rules

Consider restricting access to specific IP ranges if needed:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 80
```

## 🔄 Updates

### Updating Application Code

1. **Stop the service:**
   ```bash
   sudo systemctl stop pdf-parser.service
   ```

2. **Update files:**
   ```bash
   sudo cp new-version/*.py /opt/pdf-parser/
   sudo chown www-data:www-data /opt/pdf-parser/*.py
   ```

3. **Update dependencies if needed:**
   ```bash
   sudo -u www-data /opt/pdf-parser/venv/bin/pip install -r /opt/pdf-parser/requirements.txt
   ```

4. **Start the service:**
   ```bash
   sudo systemctl start pdf-parser.service
   ```

### Zero-Downtime Updates

For production systems, use Gunicorn's reload capability:
```bash
sudo systemctl reload pdf-parser.service
```

## 🆘 Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo journalctl -u pdf-parser.service -n 50
   ```

2. **Permission errors:**
   ```bash
   sudo chown -R www-data:www-data /opt/pdf-parser
   sudo chown -R www-data:www-data /var/log/pdf-parser
   ```

3. **Port conflicts:**
   ```bash
   sudo netstat -tlnp | grep :5000
   sudo lsof -i :5000
   ```

4. **Nginx errors:**
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

### Performance Tuning

1. **Adjust worker processes in `gunicorn.conf.py`:**
   ```python
   workers = multiprocessing.cpu_count() * 2 + 1
   ```

2. **Increase file upload limits in nginx:**
   ```nginx
   client_max_body_size 50M;
   ```

3. **Monitor resource usage:**
   ```bash
   htop
   sudo iotop
   ```

## 📞 Support

- Check logs first: `sudo journalctl -u pdf-parser.service -f`
- Test API directly: `curl http://localhost:5000/api/v1/health`
- Verify nginx config: `sudo nginx -t`

## 🔄 Backup

Important files to backup:
- `/opt/pdf-parser/` (application code)
- `/etc/nginx/sites-available/pdf-parser` (nginx config)
- `/etc/systemd/system/pdf-parser.service` (systemd service)
- SSL certificates (if using HTTPS)

## 📈 Scaling

For high-traffic deployments:
1. Increase Gunicorn workers
2. Use a load balancer (HAProxy/nginx upstream)
3. Consider containerization with Docker
4. Use a process manager like Supervisor for additional monitoring