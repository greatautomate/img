"""
Message handlers for the Telegram bot
"""

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
from loguru import logger

from ...services import BFLAPIService, ImageProcessor, UserService
from ...models import ImageEdit, EditStatus
from ...database import db
from ..middleware import UserMiddleware, LoggingMiddleware


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        user = context.user_data.get("db_user")
        
        # Get the largest photo
        photo = update.message.photo[-1]
        
        # Download photo - FIXED METHOD
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()  # Fixed: use download_as_bytearray()
        
        # Validate image
        try:
            image_info = ImageProcessor.validate_image(photo_bytes)
            logger.info(f"Image validated: {image_info}")
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Invalid Image**\n\n{str(e)}\n\n"
                "Please send a valid image (JPEG, PNG, or WEBP) under 20MB.",
                parse_mode="Markdown"
            )
            return
        
        # Store image in context
        context.user_data["pending_image"] = {
            "bytes": photo_bytes,
            "info": image_info,
            "message_id": update.message.message_id
        }
        
        # Create prompt keyboard
        keyboard = [
            [InlineKeyboardButton("🎨 Color Change", callback_data="prompt_color")],
            [InlineKeyboardButton("📝 Text Edit", callback_data="prompt_text")],
            [InlineKeyboardButton("🖼️ Background", callback_data="prompt_background")],
            [InlineKeyboardButton("✏️ Custom Prompt", callback_data="prompt_custom")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📸 **Image Received!**\n\n"
            f"**Image Info:**\n"
            f"• Format: {image_info['format']}\n"
            f"• Size: {image_info['size'][0]}×{image_info['size'][1]}\n"
            f"• File Size: {image_info['file_size_mb']:.1f}MB\n\n"
            f"Now tell me what you'd like to edit! You can:\n"
            f"• Use the quick options below\n"
            f"• Type your own custom prompt\n\n"
            f"**Example prompts:**\n"
            f"• 'Change the car color to red'\n"
            f"• 'Replace \"Hello\" with \"Welcome\"'\n"
            f"• 'Add a sunset background'",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await update.message.reply_text(
            "⚠️ Error processing your image. Please try again."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (edit prompts)"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        await LoggingMiddleware.log_interaction(update, context)
        
        user = context.user_data.get("db_user")
        
        # Check if user has a pending image
        pending_image = context.user_data.get("pending_image")
        if not pending_image:
            await update.message.reply_text(
                "📸 **Please send an image first!**\n\n"
                "I need an image to edit. Send me a photo and then tell me what you'd like to change.",
                parse_mode="Markdown"
            )
            return
        
        prompt = update.message.text.strip()
        
        if len(prompt) < 3:
            await update.message.reply_text(
                "❌ **Prompt too short**\n\n"
                "Please provide a more detailed description of what you'd like to edit.",
                parse_mode="Markdown"
            )
            return
        
        if len(prompt) > 500:
            await update.message.reply_text(
                "❌ **Prompt too long**\n\n"
                "Please keep your edit description under 500 characters.",
                parse_mode="Markdown"
            )
            return
        
        # Create image edit record
        image_edit = ImageEdit(
            user_id=user.id,
            telegram_user_id=user.telegram_user_id,
            telegram_message_id=update.message.message_id,
            prompt=prompt,
            original_image_size=len(pending_image["bytes"]),
            aspect_ratio=user.preferred_aspect_ratio,
            output_format=user.preferred_output_format
        )
        
        # Classify edit type
        image_edit.edit_type = image_edit.classify_edit_type()
        
        # Save to database
        await db.create_image_edit(image_edit)
        
        # Send processing message
        processing_message = await update.message.reply_text(
            f"🎨 **Processing your edit...**\n\n"
            f"**Prompt:** {prompt}\n"
            f"**Edit Type:** {image_edit.edit_type.replace('_', ' ').title()}\n\n"
            f"⏳ This usually takes 30-60 seconds. Please wait...",
            parse_mode="Markdown"
        )
        
        # Process the edit
        try:
            await process_image_edit(
                image_edit, 
                pending_image["bytes"], 
                update, 
                context, 
                processing_message
            )
        except Exception as e:
            logger.error(f"Error processing image edit: {e}")
            
            # Update edit status
            image_edit.fail_with_error(str(e))
            await db.update_image_edit(image_edit)
            
            # Update user stats
            await UserService.update_user_stats(
                user.telegram_user_id, 
                edit_success=False,
                edit_type=image_edit.edit_type
            )
            
            await processing_message.edit_text(
                f"❌ **Edit Failed**\n\n"
                f"**Error:** {str(e)}\n\n"
                f"Please try again with a different prompt or image.",
                parse_mode="Markdown"
            )
        
        # Clear pending image
        context.user_data.pop("pending_image", None)
        
    except Exception as e:
        logger.error(f"Error handling text: {e}")
        await update.message.reply_text(
            "⚠️ Error processing your request. Please try again."
        )


async def process_image_edit(image_edit: ImageEdit, 
                           image_bytes: bytes, 
                           update: Update, 
                           context: ContextTypes.DEFAULT_TYPE,
                           processing_message):
    """Process the image edit request"""
    
    try:
        # Convert bytearray to bytes if needed
        if isinstance(image_bytes, bytearray):
            image_bytes = bytes(image_bytes)
        
        # Encode image to base64
        input_image_base64 = BFLAPIService.encode_image_to_base64(image_bytes)
        
        # Process with BFL.ai API
        async with BFLAPIService() as bfl_service:
            # Create edit request
            request_id, polling_url = await bfl_service.create_edit_request(
                prompt=image_edit.prompt,
                input_image_base64=input_image_base64,
                aspect_ratio=image_edit.aspect_ratio,
                output_format=image_edit.output_format,
                seed=image_edit.seed,
                safety_tolerance=image_edit.safety_tolerance
            )
            
            # Update edit status
            image_edit.start_processing(request_id, polling_url)
            await db.update_image_edit(image_edit)
            
            # Wait for completion
            result = await bfl_service.wait_for_completion(polling_url)
            
            # Get edited image URL
            edited_image_url = result.get("result", {}).get("sample")
            if not edited_image_url:
                raise Exception("No edited image URL in response")
            
            # Download edited image
            edited_image_bytes = await bfl_service.download_image(edited_image_url)
            
            # Update edit status
            image_edit.complete_successfully(edited_image_url)
            await db.update_image_edit(image_edit)
            
            # Update user stats
            await UserService.update_user_stats(
                image_edit.telegram_user_id,
                edit_success=True,
                edit_type=image_edit.edit_type,
                processing_time=image_edit.processing_time_seconds
            )
            
            # Create result keyboard
            keyboard = [
                [InlineKeyboardButton("🔄 Edit Again", callback_data="edit_again")],
                [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
                [InlineKeyboardButton("ℹ️ About", callback_data="about")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send edited image
            await update.message.reply_photo(
                photo=edited_image_bytes,
                caption=f"✅ **Edit Complete!**\n\n"
                       f"**Prompt:** {image_edit.prompt}\n"
                       f"**Processing Time:** {image_edit.processing_time_seconds:.1f}s\n"
                       f"**Edit Type:** {image_edit.edit_type.replace('_', ' ').title()}\n\n"
                       f"Send another image to continue editing!",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
            # Delete processing message
            try:
                await processing_message.delete()
            except:
                pass
            
            logger.info(f"Successfully processed edit for user {image_edit.telegram_user_id}")
            
    except Exception as e:
        logger.error(f"Error in process_image_edit: {e}")
        raise


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document messages (in case user sends image as document)"""
    try:
        if not await UserMiddleware.process_user(update, context):
            return
        
        document = update.message.document
        
        # Check if it's an image document
        if not document.mime_type or not document.mime_type.startswith('image/'):
            await update.message.reply_text(
                "📄 **Document Received**\n\n"
                "I can only process images. Please send your image as a photo, not as a document.",
                parse_mode="Markdown"
            )
            return
        
        # Check file size
        if document.file_size > 20 * 1024 * 1024:  # 20MB
            await update.message.reply_text(
                "❌ **File Too Large**\n\n"
                "Please send an image smaller than 20MB.",
                parse_mode="Markdown"
            )
            return
        
        # Download and process as photo - FIXED METHOD
        document_file = await document.get_file()
        image_bytes = await document_file.download_as_bytearray()  # Fixed: use download_as_bytearray()
        
        # Validate image
        try:
            image_info = ImageProcessor.validate_image(image_bytes)
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Invalid Image**\n\n{str(e)}",
                parse_mode="Markdown"
            )
            return
        
        # Store in context (same as photo handler)
        context.user_data["pending_image"] = {
            "bytes": image_bytes,
            "info": image_info,
            "message_id": update.message.message_id
        }
        
        await update.message.reply_text(
            f"📸 **Image Document Received!**\n\n"
            f"Now tell me what you'd like to edit!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        await update.message.reply_text(
            "⚠️ Error processing your document. Please try again."
        )


async def setup_message_handlers(application, middleware):
    """Setup message handlers"""
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.IMAGE & ~filters.COMMAND, handle_document))
    
    logger.info("Message handlers setup completed")
    return True
