import os
import aiohttp
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

async def send_discord_alert(title: str, message: str, level: str = "info"):
    # Send alert to Discord via webhook

    if not DISCORD_WEBHOOK_URL:
        logging.warning("Discord webhook URL is not set.")
        return
    
    # Define colors for different alert levels
    colors = {
        "info": 0x3498db, # Blue
        "warning": 0xf1c40f, # Yellow
        "error": 0xe74c3c,  # Red
        "critical": 0x8e44ad # Purple
    }

    embed = {
        "title": f"🚨 {title}",
        "description": message,
        "color": colors.get(level, 0x3498db),
        "timestamp": datetime.utcnow().isoformat(),
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}) as resp:
                if resp.status != 204:
                    logging.error(f"❌ Error sending Discord alert: {resp.status}")
        except Exception as e:
            logging.error(f"❌ Exception sending Discord alert: {str(e)}")