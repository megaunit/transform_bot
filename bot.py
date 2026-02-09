import asyncio
import os
import json
import subprocess
import sys
import shutil
import numpy as np

import pytz
import telegram._utils.datetime as tg_datetime
import telegram.ext._jobqueue as tg_jobqueue
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


# Get the absolute path of the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Create media directory for outputs
media_dir = os.path.join(script_dir, "media", "videos", "transformation", "1080p60")
print(f"Media dir: {media_dir}")
# Create necessary directories
os.makedirs(media_dir, exist_ok=True)

# APScheduler 3 requires pytz timezones; PTB defaults to datetime.timezone.utc
tg_datetime.UTC = pytz.UTC
tg_jobqueue.UTC = pytz.UTC

# Define config file path
CONFIG_FILE = os.path.join(script_dir, "config.json")
TOKEN_FILE = os.path.join(script_dir, "token.txt")

def load_bot_token():
    """Load bot token from env or token.txt."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        return token.strip()
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading token file: {str(e)}")
        return None

def ensure_config_file():
    """Create config.json if it doesn't exist"""
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({}, f)
            print(f"Created new config file at: {CONFIG_FILE}")
        except Exception as e:
            print(f"Error creating config file: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text('Welcome to <b>Linear Transformation</b> Bot!\n\nTo visualize a linear transformation, please send a 2x2 matrix in following form:\n<code>a11 a12\na21 a22</code>\n\nTo include a function in the visualization, use the /function command followed by the function expression.', parse_mode=ParseMode.HTML)

async def set_function(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save the user's function to the config file"""
    try:
        if not update.message or not update.effective_chat:
            return
            
        channel_id = str(update.effective_chat.id)
        # Get the function string after the command
        func_str = " ".join(context.args)
        
        if not func_str:
            await update.message.reply_text('Usage: /function <function_expression>\nTo remove the function, pass function as "None"\n\nNote: function must be in terms of x only')
            return

        if "y" in func_str:
            await update.message.reply_text('Error: Function must be in terms of x only (no y allowed).')
            return

        # Update the config
        ensure_config_file()
        config = {}
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            config = {}
            
        # Ensure user entry exists
        if channel_id not in config:
            config[channel_id] = {}
        
        # Handle legacy list format if encountered
        if isinstance(config[channel_id], list):
            config[channel_id] = {"matrix": config[channel_id]}
            
        config[channel_id]["function"] = func_str
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
            
        await update.message.reply_text(f"Function saved: {func_str}\nTo remove function use /function None")

    except Exception as e:
        print(f"Error in set_function: {str(e)}")
        if update.message:
            await update.message.reply_text("An error occurred while saving the function.")

async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not update.message:
            return
        # Get the channel ID to identify this request uniquely
        channel_id = update.effective_chat.id
        
        # Extract user input from the message (Matrix only)
        try:
            matrix_lines = update.message.text.strip().split("\n")
            for row_num, row in enumerate(matrix_lines):
                matrix_lines[row_num] = row.split(" ")
                
            matrix = [[float(x) for x in row] for row in matrix_lines]
            if not (len(np.array(matrix).flatten()) == 4):
                raise ValueError("Matrix must be a list of 4 elements")

        except Exception as e:
            await update.message.reply_text("Something wrong happened, make sure format is correct:\na11 a12\na21 a22")
            print(f"Parsing error: {str(e)}")
            return

        # Generate the Manim scene based on user input and channel ID
        update_user_data(channel_id, matrix)
        
        # Send "processing" message
        processing_message = await update.message.reply_text("Processing your matrix... This may take a moment.")
        
        # Create the video
        success = await asyncio.to_thread(create_manim_scene, channel_id)
        if not success:
            await context.bot.edit_message_text(
                chat_id=channel_id,
                message_id=processing_message.message_id,
                text="Failed to generate video. Please try again."
            )
            return
        
        # Construct output video path
        output_video_path = os.path.join(media_dir, f"output_{channel_id}.mp4")
        print(f"Output Video Path: {output_video_path}")
        # Check if video exists and has content
        if not os.path.exists(output_video_path) or os.path.getsize(output_video_path) == 0:
            await context.bot.edit_message_text(
                chat_id=channel_id,
                message_id=processing_message.message_id,
                text="Video file not found. Please try again."
            )
            return
        
        # Send the generated video back to the user
        with open(output_video_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=channel_id, video=video_file)
            
        # Delete the processing message
        await context.bot.delete_message(
            chat_id=channel_id,
            message_id=processing_message.message_id
        )

        
        # Clean up files
        try:
            if os.path.exists(output_video_path):
                os.remove(output_video_path)
                shutil.rmtree(os.path.join(os.path.dirname(output_video_path), "partial_movie_files"))
                print(f"Deleted output video: {output_video_path}")
                
            temp_dir = os.path.join(media_dir, "videos", "transformation", "1080p60")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print("Cleaned up temporary Manim files")
                
        except Exception as e:
            print(f"Failed to clean up files: {str(e)}")
            
        
    except Exception as e:
        print(f"Error in generate_video: {str(e)}")
        if update.message:
            await update.message.reply_text("An error occurred while processing your request.")

def update_user_data(channel_id, matrix):
    """Update the config file with new user data"""
    try:
        # Ensure config file exists
        ensure_config_file()
        
        # Read existing config
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            config = {}
        except Exception as e:
            print(f"Error reading config file: {str(e)}")
            config = {}
        
        # Update the config with the user's matrix
        config.setdefault(str(channel_id), {})
        config[str(channel_id)].setdefault("function", "None")
        config[str(channel_id)]["matrix"] = matrix
        
        print(f"Updating config for channel {channel_id}")
        print(f"New matrix: {matrix}")
        print(f"Config after update: {config}")
        
        # Write the updated data back to the JSON file
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            print(f"Successfully wrote to config file: {CONFIG_FILE}")
        except Exception as e:
            print(f"Error writing to config file: {str(e)}")

    except Exception as e:
        print(f"Error in update_user_data: {str(e)}")
        raise

def create_manim_scene(channel_id):
    try:
        # Prefer an explicit override, otherwise run Manim from the current Python env
        # This keeps it portable across machines/conda envs.
        manim_cmd = os.environ.get("MANIM_CMD")
        if manim_cmd:
            command = [manim_cmd]
        else:
            command = [sys.executable, "-m", "manim"]

        command += [
            # "--media_dir", media_dir,
            "-v", "WARNING",
            os.path.join(script_dir, "transformation.py"),
            "Plane",
            "-o", f"output_{channel_id}.mp4",
            str(channel_id)
        ]
        
        # Prepare environment with current python's bin dir AND script dir in PATH
        env = os.environ.copy()
        current_bin_dir = os.path.dirname(sys.executable)
        env["PATH"] = script_dir + os.pathsep + current_bin_dir + os.pathsep + env.get("PATH", "")

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        print("Manim stdout:", result.stdout)
        print("Manim stderr:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error in create_manim_scene: {str(e)}")
        return False

def main():
    ensure_config_file()
    
    print(f"Script directory: {script_dir}")
    print(f"Config file location: {CONFIG_FILE}")
    print(f"Media directory: {media_dir}")
    
    token = load_bot_token()
    if not token:
        raise RuntimeError("Bot token not found. Set TELEGRAM_BOT_TOKEN or put it in token.txt.")
    
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("function", set_function))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_video))
    
    print("Bot started successfully!")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
