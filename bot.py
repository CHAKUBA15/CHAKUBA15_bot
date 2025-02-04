import logging
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATIE ---
TELEGRAM_BOT_TOKEN = "7472334939:AAErSoTRmt1Lo2TVlg0pROseVzGiu333yNI"
DEX_SCREENER_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

# Telegram Bot Initialiseren
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO)

# --- FUNCTIE: Coins ophalen ---
def get_solana_trades():
    response = requests.get(DEX_SCREENER_API)
    if response.status_code == 200:
        data = response.json()
        tokens = []
        
        for pair in data['pairs']:
            market_cap = pair['baseToken']['liquidity']
            volume = pair['volume']['h24']
            buyers = pair['txns']['h24']['buys']
            sellers = pair['txns']['h24']['sells']
            
            # Criteria: Market Cap, Volume, Kopers vs Verkoper Ratio
            if market_cap and float(market_cap) > 50000 and float(volume) > 10000 and buyers > (sellers * 2):
                tokens.append({
                    "name": pair['baseToken']['name'],
                    "symbol": pair['baseToken']['symbol'],
                    "price": pair['priceUsd'],
                    "link": pair['url']
                })
        return tokens
    return []

# --- TELEGRAM BOT: Stuur trading signals ---
@bot.message_handler(commands=['start'])
def send_trade_signals(message):
    tokens = get_solana_trades()
    
    if not tokens:
        bot.send_message(message.chat.id, "Geen goede trade kansen gevonden op dit moment.")
        return
    
    for token in tokens[:5]:  # Max 5 signalen tegelijk sturen
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("✅ Kopen", callback_data=f"buy_{token['symbol']}"),
            InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_{token['symbol']}")
        )
        
        message_text = f"🔥 *Nieuwe Solana Trade!* 🔥\n\n"
        message_text += f"📌 *{token['name']}* ({token['symbol']})\n"
        message_text += f"💰 Prijs: ${token['price']}\n"
        message_text += f"🔗 [Bekijk op Dex Screener]({token['link']})\n"
        
        bot.send_message(message.chat.id, message_text, parse_mode="Markdown", reply_markup=markup)

# --- TELEGRAM BOT: Knoppen Acties ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if "buy_" in call.data:
        token = call.data.split("buy_")[1]
        bot.send_message(call.message.chat.id, f"✅ Je hebt {token} gekocht!")
    elif "skip_" in call.data:
        token = call.data.split("skip_")[1]
        bot.send_message(call.message.chat.id, f"⏭️ {token} overgeslagen.")

# --- BOT STARTEN ---
if __name__ == "__main__":
    bot.polling(none_stop=True)
