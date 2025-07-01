# MedusaXD AI Image Editor Bot - API Documentation

## Overview

MedusaXD AI Image Editor Bot is a Telegram bot that provides AI-powered image editing capabilities using BFL.ai's FLUX.1 Kontext [pro] model. This document describes the bot's functionality, commands, and technical implementation.

## Bot Commands

### User Commands

#### `/start`
- **Description**: Initialize the bot and show welcome message
- **Usage**: `/start`
- **Response**: Welcome message with bot introduction and quick action buttons

#### `/help`
- **Description**: Display help information and usage instructions
- **Usage**: `/help`
- **Response**: Detailed help message with examples and tips

#### `/stats`
- **Description**: Show user's personal statistics
- **Usage**: `/stats`
- **Response**: User's edit history, success rate, and favorite edit types

#### `/about`
- **Description**: Display information about the bot
- **Usage**: `/about`
- **Response**: Bot version, technology stack, and credits

#### `/cancel`
- **Description**: Cancel current operation and clear context
- **Usage**: `/cancel`
- **Response**: Confirmation of cancellation

### Admin Commands

#### `/admin_stats`
- **Description**: View bot-wide analytics (admin only)
- **Usage**: `/admin_stats`
- **Response**: Global statistics including total users, edits, and success rates

#### `/ban <user_id>`
- **Description**: Ban a user from using the bot (admin only)
- **Usage**: `/ban 123456789`
- **Response**: Confirmation of user ban

#### `/unban <user_id>`
- **Description**: Unban a previously banned user (admin only)
- **Usage**: `/unban 123456789`
- **Response**: Confirmation of user unban

#### `/admin_help`
- **Description**: Show admin commands help (admin only)
- **Usage**: `/admin_help`
- **Response**: List of available admin commands

## Image Editing Workflow

### 1. Send Image
Users send an image to the bot in one of the supported formats:
- **Supported formats**: JPEG, PNG, WEBP
- **Maximum size**: 20MB
- **Maximum resolution**: 20 megapixels

### 2. Provide Edit Prompt
After sending an image, users provide a text description of the desired edit:
- **Minimum length**: 3 characters
- **Maximum length**: 500 characters
- **Language**: English (recommended)

### 3. Processing
The bot processes the edit request:
- Validates the image and prompt
- Sends request to BFL.ai API
- Polls for completion (typically 30-60 seconds)
- Downloads and returns the edited image

### 4. Result
Users receive:
- The edited image
- Processing time information
- Options for additional actions

## Edit Types and Examples

### Color Changes
- **Example**: "Change the car color to red"
- **Use case**: Modify object colors while preserving other elements

### Text Editing
- **Example**: "Replace 'Hello' with 'Welcome'"
- **Use case**: Modify text within images
- **Tip**: Use quotes around specific text for better accuracy

### Object Modification
- **Example**: "Remove the person from the image"
- **Use case**: Add or remove objects from scenes

### Background Changes
- **Example**: "Add a sunset background"
- **Use case**: Modify or replace image backgrounds

### Style Changes
- **Example**: "Make it look like a painting"
- **Use case**: Apply artistic styles or effects

## API Integration

### BFL.ai FLUX.1 Kontext [pro] API

The bot integrates with BFL.ai's image editing API:

#### Endpoint
```
POST https://api.bfl.ai/v1/flux-kontext-pro
```

#### Request Parameters
- `prompt` (string): Edit description
- `input_image` (string): Base64 encoded image
- `aspect_ratio` (string): Output aspect ratio (default: "1:1")
- `output_format` (string): Output format ("jpeg" or "png")
- `safety_tolerance` (integer): Content moderation level (0-2)

#### Response
```json
{
  "id": "request_id",
  "polling_url": "https://api.bfl.ai/v1/results/request_id"
}
```

#### Polling for Results
```
GET https://api.bfl.ai/v1/results/request_id
```

#### Result Response
```json
{
  "status": "Ready",
  "result": {
    "sample": "https://signed-url-to-image.jpg"
  }
}
```

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  telegram_user_id: Number,
  username: String,
  first_name: String,
  last_name: String,
  language_code: String,
  preferred_aspect_ratio: String,
  preferred_output_format: String,
  created_at: Date,
  updated_at: Date,
  last_seen: Date,
  stats: {
    total_edits: Number,
    successful_edits: Number,
    failed_edits: Number,
    favorite_edit_types: Object,
    last_edit_date: Date
  },
  is_active: Boolean,
  is_premium: Boolean,
  is_banned: Boolean
}
```

### Image Edits Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  telegram_user_id: Number,
  telegram_message_id: Number,
  prompt: String,
  original_image_size: Number,
  bfl_request_id: String,
  bfl_polling_url: String,
  aspect_ratio: String,
  output_format: String,
  edited_image_url: String,
  status: String, // pending, processing, completed, failed, cancelled
  created_at: Date,
  started_at: Date,
  completed_at: Date,
  processing_time_seconds: Number,
  error_message: String,
  retry_count: Number,
  edit_type: String,
  tags: Array
}
```

### Analytics Collection
```javascript
{
  _id: ObjectId,
  total_users: Number,
  total_edits: Number,
  successful_edits: Number,
  failed_edits: Number,
  average_processing_time: Number,
  success_rate: Number,
  popular_edit_types: Object,
  popular_aspect_ratios: Object,
  popular_output_formats: Object,
  daily_stats: Array,
  created_at: Date,
  updated_at: Date
}
```

## Error Handling

### Common Error Scenarios

#### Invalid Image
- **Cause**: Unsupported format, too large, corrupted
- **Response**: Error message with specific issue and guidance

#### API Errors
- **Cause**: BFL.ai API issues, network problems
- **Response**: User-friendly error message, automatic retry for transient errors

#### Rate Limiting
- **Cause**: Too many requests from user
- **Response**: Rate limit warning with cooldown period

#### Processing Timeout
- **Cause**: API processing takes too long
- **Response**: Timeout message with option to retry

## Security Features

### User Authentication
- Telegram user ID verification
- Admin user whitelist
- Banned user blacklist

### Content Moderation
- BFL.ai built-in safety filters
- Configurable safety tolerance levels
- Automatic content flagging

### Data Protection
- No permanent image storage
- Encrypted database connections
- Secure API key management

## Performance Metrics

### Response Times
- **Image validation**: < 1 second
- **API request creation**: < 2 seconds
- **Image processing**: 30-60 seconds (BFL.ai dependent)
- **Result delivery**: < 5 seconds

### Throughput
- **Concurrent users**: Scalable based on deployment
- **Daily edits**: No hard limits (API quota dependent)
- **Success rate**: Target > 95%

## Deployment Options

### Local Development
```bash
python main.py
```

### Docker
```bash
docker build -t medusaxd-bot .
docker run -d --env-file .env medusaxd-bot
```

### Docker Compose
```bash
docker-compose up -d
```

### Render.com
- Background Worker service
- Automatic deployment from Git
- Environment variable configuration

## Environment Variables

### Required
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `BFL_API_KEY`: API key from BFL.ai
- `MONGODB_URL`: MongoDB connection string

### Optional
- `BOT_USERNAME`: Bot username (default: MedusaXDAIBot)
- `ENVIRONMENT`: Deployment environment (development/production)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `ADMIN_USER_IDS`: Comma-separated admin user IDs

## Monitoring and Logging

### Logging Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning conditions
- **ERROR**: Error conditions requiring attention

### Log Files
- `medusaxd_bot.log`: General application logs
- `medusaxd_bot_errors.log`: Error-specific logs

### Health Checks
- Database connectivity
- API availability
- Service status endpoints

## Rate Limits and Quotas

### BFL.ai API Limits
- **Cost**: $0.04 per image edit
- **Rate limits**: As per BFL.ai terms
- **Image size**: Max 20MB/20 megapixels

### Bot Limits
- **User rate limit**: 10 requests per minute (configurable)
- **Concurrent processing**: Based on deployment resources
- **Storage**: Temporary only, no permanent image storage
