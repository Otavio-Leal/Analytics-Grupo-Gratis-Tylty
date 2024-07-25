import os
from telethon import TelegramClient, events
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import requests
import pytz
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Leitura das variáveis de ambiente
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
channel_id = int(os.getenv('CHANNEL_ID'))
admin_group_id = int(os.getenv('ADMIN_GROUP_ID'))
post_url = os.getenv('POST_URL')
auth_token = os.getenv('AUTH_TOKEN')

client = TelegramClient('session_name', api_id, api_hash)

# Definir o fuso horário UTC-4
local_tz = pytz.timezone('America/Asuncion')

# Custom formatter to use local timezone for logging
class UTCMinus4Formatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=pytz.utc).astimezone(local_tz)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            try:
                s = dt.isoformat(timespec='milliseconds')
            except TypeError:
                s = dt.isoformat()
        return s

# Configuração básica de log com rotação diária
log_directory = '/app/logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file = os.path.join(log_directory, 'telegram_bot.log')
file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1)
file_handler.suffix = "%Y-%m-%d"
file_handler.setLevel(logging.INFO)


log_file = os.path.join(log_directory, 'telegram_bot.log')
file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=30)
file_handler.suffix = "%Y-%m-%d"
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = UTCMinus4Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)
logger.info('Logging setup complete')

def convert_to_utc_minus_4(dt):
    return dt.astimezone(local_tz).strftime('%Y-%m-%dT%H:%M:%S')

async def send_alert(message):
    try:
        await client.send_message(admin_group_id, message)
    except Exception as e:
        logging.error(f"Failed to send alert message: {e}")

@client.on(events.ChatAction)
async def handler(event):
    if event.chat_id != channel_id:
        return  # Ignora eventos de outros canais

    user = await event.get_user()
    if not user:
        logging.warning("User is None, skipping event")
        return

    channel = await event.get_chat()
    if not channel:
        logging.warning("Channel is None, skipping event")
        return

    if event.action_message:
        timestamp = convert_to_utc_minus_4(event.action_message.date)
    else:
        timestamp = convert_to_utc_minus_4(event.original_update.date) if hasattr(event.original_update, 'date') else convert_to_utc_minus_4(datetime.now())

    logging.info(f"Timestamp do evento: {timestamp}")

    user_info = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "is_bot": user.bot,
        "timestamp": timestamp,
        "channel_name": channel.title
    }

    if event.user_joined or event.user_added:
        user_info["status"] = "joined"
    elif event.user_left or event.user_kicked:
        user_info["status"] = "left"
    else:
        return

    logging.info(f"User Info: {user_info}")
    
    headers = {
        'Authorization': auth_token
    }

    try:
        response = requests.post(post_url, json=user_info, headers=headers)
        response.raise_for_status()
        logging.info(f"Data posted successfully: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to post data: {e}")
        await send_alert(f"Failed to post data: {e}")

async def main():
    await client.start(bot_token=os.getenv('BOT_TOKEN'))
    await send_alert("Bot iniciado. Monitorando eventos do canal...")
    logging.info("Bot iniciado. Monitorando eventos do canal...")
    try:
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Bot stopped due to error: {e}")
        await send_alert(f"Bot stopped due to error: {e}")
        raise

if __name__ == '__main__':
    client.loop.run_until_complete(main())