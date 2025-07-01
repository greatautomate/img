# MedusaXD AI Image Editor Bot

A powerful Telegram bot that leverages BFL.ai's FLUX.1 Kontext [pro] model for advanced AI-powered image editing capabilities.

## Features

- 🎨 **AI-Powered Image Editing**: Transform images with simple text prompts
- 🔄 **Smart Changes**: Apply edits that seamlessly blend with existing content
- 📝 **Text in Images**: Add or modify text directly within images
- 💾 **MongoDB Integration**: Store user data and image history
- 🚀 **Scalable Deployment**: Ready for Render.com and Docker deployment
- 🛡️ **Robust Error Handling**: Comprehensive error management and user feedback

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB Atlas database (your existing mongodb.com account)
- Telegram Bot Token (from @BotFather)
- BFL.ai API Key

### Environment Variables

Create a `.env` file with the following variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BFL_API_KEY=your_bfl_api_key
MONGODB_URL=your_mongodb_atlas_connection_string
BOT_USERNAME=MedusaXDAIBot
ENVIRONMENT=production
```

**Note**: Use your existing MongoDB Atlas connection string from mongodb.com. The bot will automatically create necessary collections and indexes.

### Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run the bot: `python main.py`

### Docker Deployment

```bash
docker build -t medusaxd-bot .
docker run -d --env-file .env medusaxd-bot
```

### Render.com Deployment

1. Connect your GitHub repository to Render.com
2. Create a new Background Worker service
3. Set environment variables in Render dashboard
4. Deploy automatically on push to main branch

## Usage

1. Start a conversation with the bot: `/start`
2. Send an image to the bot
3. Follow up with a text prompt describing the edit you want
4. Wait for the AI to process and return your edited image

## Project Structure

```
medusaimg/
├── src/
│   ├── bot/
│   │   ├── handlers/
│   │   └── middleware/
│   ├── services/
│   ├── models/
│   └── utils/
├── tests/
├── docker/
├── docs/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── render.yaml
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support and questions, contact the development team or create an issue in the repository.
