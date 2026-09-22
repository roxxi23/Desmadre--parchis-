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

    if len(game["players"]) >= 2:
        game["started"] = True

await update.message.reply_text(
    f"🎉 {user.full_name} se unió a la partida.\n"
    f"👥 Jugadores: {len(game['players'])}/4\n\n"
    "🎲 ¡Ya pueden empezar con /tirar!"
)


async def salir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if partida_expirada(chat_id):
        await update.message.reply_text(
            "⏰ La partida ya estaba abandonada y fue cerrada."
        )
        return

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No hay una partida activa."
        )
        return

    game = games[chat_id]

    if user.id not in game["players"]:
        await update.message.reply_text(
            "😂 No estás en la partida."
        )
        return

    game["players"].remove(user.id)
    game["names"].pop(user.id, None)
    game["positions"].pop(user.id, None)

    if len(game["players"]) == 0:
        del games[chat_id]

        await update.message.reply_text(
            "🎲 La partida terminó y quedó liberada.\n"
            "Ya pueden crear otra con /parchis."
        )
        return

    actualizar_actividad(chat_id)

    game["turn"] = game["turn"] % len(game["players"])

    await update.message.reply_text(
        f"🚪 {user.full_name} salió de la partida."
    )


async def reiniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No hay ninguna partida activa."
        )
        return

    del games[chat_id]

    await update.message.reply_text(
        "🧹🎲 ¡Partida cancelada!\n\n"
        "La mesa quedó liberada.\n"
        "Ya pueden comenzar una nueva con /parchis ❤️"
    )


async def tirar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if partida_expirada(chat_id):
        await update.message.reply_text(
            "⏰ La partida estuvo demasiado tiempo sin actividad "
            "y fue cerrada.\n\n"
            "🎲 Usá /parchis para crear una nueva."
        )
        return

    if chat_id not in games:
        await update.message.reply_text(
            "❌ Primero creá una partida con /parchis."
        )
        return

    game = games[chat_id]

    if len(game["players"]) < 2:
        actualizar_actividad(chat_id)

        await update.message.reply_text(
            "👥 Necesitamos al menos 2 jugadores.\n"
            "Usá /unirme para entrar."
        )
        return

    current_player = game["players"][game["turn"]]

    if user.id != current_player:
        nombre = game["names"][current_player]

        await update.message.reply_text(
            "⏳ Todavía no te toca.\n"
            f"🎲 Es el turno de {nombre}."
        )
        return

    dado = random.randint(1, 6)

    game["positions"][user.id] += dado
    posicion = game["positions"][user.id]

    actualizar_actividad(chat_id)

    await update.message.reply_text(
        f"🎲 {user.full_name} tiró el dado...\n\n"
        f"🎲 ¡Salió un {dado}!\n"
        f"📍 Avanzás a la posición {posicion}."
    )

    game["turn"] = (
        game["turn"] + 1
    ) % len(game["players"])

    siguiente = game["players"][game["turn"]]
    nombre_siguiente = game["names"][siguiente]

    await update.message.reply_text(
        f"👉 Ahora le toca a {nombre_siguiente}.\n"
        "🎲 Usá /tirar"
    )


async def tablero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if partida_expirada(chat_id):
        await update.message.reply_text(
            "⏰ La partida estuvo demasiado tiempo sin actividad "
            "y fue cerrada.\n\n"
            "🎲 Usá /parchis para crear una nueva."
        )
        return

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No hay una partida activa."
        )
        return

    game = games[chat_id]
    actualizar_actividad(chat_id)

    texto = "🏆🎲 TABLERO DESMADRE PARCHÍS 🎲🏆\n\n"

    for user_id in game["players"]:
        nombre = game["names"][user_id]
        posicion = game["positions"][user_id]

        texto += f"👤 {nombre}: 📍 {posicion}\n"

    await update.message.reply_text(texto)


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲❤️ DESMADRE PARCHÍS ❤️🎲\n\n"
        "/parchis — Crear una partida\n"
        "/unirme — Unirme a la partida\n"
        "/salir — Salir de la partida\n"
        "/reiniciar — Cancelar una partida trabada\n"
        "/tirar — Tirar el dado\n"
        "/tablero — Ver el tablero\n"
        "/ayuda — Cómo jugar\n\n"
        "👥 De 2 a 4 jugadores\n"
        "⏰ Las partidas sin actividad se liberan después de 30 minutos.\n"
        "🎲 ¡Que empiece el desmadre!"
    )


def main():
    token = os.environ["TELEGRAM_TOKEN"]

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("parchis", parchis))
    app.add_handler(CommandHandler("unirme", unirme))
    app.add_handler(CommandHandler("salir", salir))
    app.add_handler(CommandHandler("reiniciar", reiniciar))
    app.add_handler(CommandHandler("tirar", tirar))
    app.add_handler(CommandHandler("tablero", tablero))
    app.add_handler(CommandHandler("ayuda", ayuda))

    print("🎲 Desmadre Parchís está funcionando...")

    app.run_polling()


if __name__ == "__main__":
    main()
