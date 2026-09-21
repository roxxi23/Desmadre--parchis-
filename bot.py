import os
import random
import time

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

games = {}

# Tiempo máximo sin actividad: 30 minutos
GAME_TIMEOUT = 30 * 60


def partida_expirada(chat_id):
    if chat_id not in games:
        return False

    ultima_actividad = games[chat_id].get("last_activity", time.time())

    if time.time() - ultima_actividad >= GAME_TIMEOUT:
        del games[chat_id]
        return True

    return False


def actualizar_actividad(chat_id):
    if chat_id in games:
        games[chat_id]["last_activity"] = time.time()


async def parchis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if partida_expirada(chat_id):
        await update.message.reply_text(
            "🧹 La partida anterior estaba abandonada y fue cerrada.\n\n"
            "🎲 ¡Ya pueden comenzar una nueva partida!"
        )

    if chat_id in games:
        actualizar_actividad(chat_id)

        await update.message.reply_text(
            "🎲 Ya hay una partida creada.\n"
            "Usá /unirme para entrar.\n\n"
            "🧹 Si la partida quedó abandonada, usá /reiniciar."
        )
        return

    games[chat_id] = {
        "players": [user.id],
        "names": {user.id: user.full_name},
        "turn": 0,
        "positions": {user.id: 0},
        "started": False,
        "last_activity": time.time()
    }

    await update.message.reply_text(
        "🎲❤️ ¡NUEVA PARTIDA DE DESMADRE PARCHÍS! ❤️🎲\n\n"
        f"👤 {user.full_name} creó la partida.\n\n"
        "👥 Los demás jugadores pueden entrar con /unirme\n"
        "🏆 Cuando haya al menos 2 jugadores, empieza con /tirar"
    )


async def unirme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if partida_expirada(chat_id):
        await update.message.reply_text(
            "⏰ La partida anterior estuvo demasiado tiempo sin actividad "
            "y fue cerrada.\n\n"
            "🎲 Usá /parchis para crear una nueva."
        )
        return

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No hay ninguna partida.\n"
            "Usá /parchis para crear una."
        )
        return

    game = games[chat_id]
    actualizar_actividad(chat_id)

    if user.id in game["players"]:
        await update.message.reply_text("😂 Ya estás jugando.")
        return

    if len(game["players"]) >= 4:
        await update.message.reply_text(
            "❌ La partida ya tiene 4 jugadores."
        )
        return

    game["players"].append(user.id)
    game["names"][user.id] = user.full_name
    game["positions"][user.id] = 0

    if
