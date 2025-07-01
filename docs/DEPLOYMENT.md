# MedusaXD AI Image Editor Bot - Deployment Guide

## Overview

This guide covers various deployment options for the MedusaXD AI Image Editor Bot, from local development to production deployment on cloud platforms.

## Prerequisites

### Required Accounts and Services

1. **Telegram Bot Token**
   - Create a bot via [@BotFather](https://t.me/BotFather)
   - Save the bot token securely

2. **BFL.ai API Key**
   - Sign up at [BFL.ai](https://bfl.ai)
   - Get API key from dashboard
   - Ensure sufficient credits for image processing

3. **MongoDB Database**
   - MongoDB Atlas (recommended for production)
   - Local MongoDB instance
   - Docker MongoDB container

### System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM
- **Storage**: 1GB free space
- **Network**: Stable internet connection

## Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd medusaimg
```

### 2. Run Setup Script
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Configure Environment
Edit `.env` file with your credentials:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
BFL_API_KEY=your_bfl_api_key_here
MONGODB_URL=your_mongodb_connection_string
ADMIN_USER_IDS=your_telegram_user_id
```

### 4. Run Locally
```bash
./scripts/deploy.sh local
```

## Docker Deployment

### Single Container Deployment

#### 1. Build Image
```bash
docker build -t medusaxd-bot .
```

#### 2. Run Container
```bash
docker run -d \
  --name medusaxd-ai-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  medusaxd-bot
```

#### 3. Check Status
```bash
docker logs medusaxd-ai-bot
docker ps
```

### Docker Compose Deployment

#### 1. Configure Environment
Create `.env` file with all required variables.

#### 2. Start Services
```bash
docker-compose up -d
```

#### 3. Monitor Services
```bash
docker-compose ps
docker-compose logs -f medusaxd-bot
```

#### 4. Stop Services
```bash
docker-compose down
```

## Render.com Deployment

### 1. Prepare Repository

Ensure your code is pushed to GitHub:
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create Render Service

1. Go to [Render.com](https://render.com)
2. Connect your GitHub account
3. Create new "Background Worker" service
4. Select your repository
5. Configure build and start commands:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

### 3. Set Environment Variables

In Render dashboard, add these environment variables:
- `TELEGRAM_BOT_TOKEN`
- `BFL_API_KEY`
- `MONGODB_URL`
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `ADMIN_USER_IDS` (optional)

### 4. Deploy

Click "Deploy" and monitor the deployment logs.

### 5. Optional: Add Web Service

For health checks and webhooks:
1. Create new "Web Service"
2. Same repository and build command
3. **Start Command**: `python -m src.web.app`
4. Same environment variables

## MongoDB Setup

### MongoDB Atlas (Recommended)

1. **Create Cluster**
   - Go to [MongoDB Atlas](https://cloud.mongodb.com)
   - Create free cluster
   - Choose cloud provider and region

2. **Configure Access**
   - Add IP address to whitelist (0.0.0.0/0 for development)
   - Create database user
   - Get connection string

3. **Connection String Format**
   ```
   mongodb+srv://username:password@cluster.mongodb.net/medusaxd_bot?retryWrites=true&w=majority
   ```

### Local MongoDB

#### Using Docker
```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:7.0
```

#### Connection String
```
mongodb://admin:password@localhost:27017/medusaxd_bot?authSource=admin
```

## Production Deployment Best Practices

### Security

1. **Environment Variables**
   - Never commit secrets to version control
   - Use secure environment variable management
   - Rotate API keys regularly

2. **Database Security**
   - Use strong passwords
   - Enable authentication
   - Restrict network access
   - Enable encryption at rest

3. **Bot Security**
   - Set admin user IDs
   - Monitor for abuse
   - Implement rate limiting

### Monitoring

1. **Logging**
   - Configure appropriate log levels
   - Set up log rotation
   - Monitor error logs

2. **Health Checks**
   - Implement health check endpoints
   - Monitor service availability
   - Set up alerting

3. **Metrics**
   - Track user engagement
   - Monitor API usage
   - Measure performance

### Scaling

1. **Horizontal Scaling**
   - Multiple bot instances
   - Load balancing
   - Shared database

2. **Vertical Scaling**
   - Increase memory/CPU
   - Optimize database queries
   - Cache frequently accessed data

## Environment-Specific Configurations

### Development
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
POLLING_INTERVAL_SECONDS=1
MAX_POLLING_ATTEMPTS=30
```

### Staging
```env
ENVIRONMENT=staging
LOG_LEVEL=INFO
POLLING_INTERVAL_SECONDS=2
MAX_POLLING_ATTEMPTS=100
```

### Production
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
POLLING_INTERVAL_SECONDS=2
MAX_POLLING_ATTEMPTS=150
```

## Troubleshooting

### Common Issues

#### Bot Not Responding
1. Check bot token validity
2. Verify network connectivity
3. Check Telegram API status
4. Review application logs

#### Database Connection Errors
1. Verify MongoDB URL format
2. Check network connectivity
3. Validate credentials
4. Ensure database exists

#### BFL.ai API Errors
1. Verify API key
2. Check account credits
3. Review rate limits
4. Monitor API status

#### Image Processing Failures
1. Check image format support
2. Verify image size limits
3. Review prompt guidelines
4. Check API response

### Log Analysis

#### Error Patterns
```bash
# Check for specific errors
grep "ERROR" logs/medusaxd_bot.log

# Monitor real-time logs
tail -f logs/medusaxd_bot.log

# Check database errors
grep "database" logs/medusaxd_bot_errors.log
```

#### Performance Monitoring
```bash
# Check processing times
grep "processing_time" logs/medusaxd_bot.log

# Monitor API calls
grep "BFL.ai" logs/medusaxd_bot.log

# Check user activity
grep "User interaction" logs/medusaxd_bot.log
```

## Backup and Recovery

### Database Backup
```bash
# MongoDB dump
mongodump --uri="your_mongodb_url" --out=backup/

# Restore
mongorestore --uri="your_mongodb_url" backup/
```

### Configuration Backup
- Backup `.env` files securely
- Document environment variables
- Version control configuration files

## Maintenance

### Regular Tasks

1. **Update Dependencies**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Clean Logs**
   ```bash
   find logs/ -name "*.log" -mtime +30 -delete
   ```

3. **Monitor Resources**
   - Check disk space
   - Monitor memory usage
   - Review API quotas

4. **Security Updates**
   - Update base Docker images
   - Patch system dependencies
   - Review access logs

### Scheduled Maintenance

1. **Weekly**
   - Review error logs
   - Check performance metrics
   - Update documentation

2. **Monthly**
   - Update dependencies
   - Review security settings
   - Backup configurations

3. **Quarterly**
   - Performance optimization
   - Security audit
   - Disaster recovery testing
