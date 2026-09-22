import os
import random
import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)


TOKEN = os.getenv("TELEGRAM_TOKEN")

META = 60
GAME_TIMEOUT = 30 * 60

games = {}
scores = {}

def partida_expirada(chat_id):
    if chat_id not in games:
        return False

    ultima_actividad = games[chat_id].get("last_activity", time.time())

    if time.time() - ultima_actividad > GAME_TIMEOUT:
        del games[chat_id]
        return True

    return False


def actualizar_actividad(chat_id):
    if chat_id in games:
        games[chat_id]["last_activity"] = time.time()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 ¡Hola! Soy el bot de Parchís.\n\n"
        "Usá /ayuda para ver los comandos."
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 COMANDOS DEL PARCHÍS 🎲\n\n"
        "/parchis - Crear una partida\n"
        "/unirme - Unirse a la partida\n"
        "/salir - Salir de la partida\n"
        "/tirar - Tirar el dado\n"
        "/tablero - Ver el tablero\n"
        "/reiniciar - Cancelar la partida\n"
        "/cancelar - Cancelar la partida\n"
        "/ayuda - Ver esta ayuda"
    )


async def parchis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    partida_expirada(chat_id)

    if chat_id in games:
        await update.message.reply_text(
            "🎲 Ya hay una partida activa.\n\n"
            "Usá /unirme para entrar."
        )
        return

    games[chat_id] = {
        "players": [user.id],
        "names": {
            user.id: user.full_name
        },
        "positions": {
            user.id: 0
        },
        "turn": 0,
        "started": False,
        "created_at": time.time(),
        "last_activity": time.time(),
    }

    await update.message.reply_text(
        f"🎲 ¡{user.full_name} creó una partida de Parchís!\n\n"
        "👥 Jugadores: 1/4\n"
        "👉 Usá /unirme para entrar."
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
            "❌ No hay ninguna partida.\n\n"
            "🎲 Usá /parchis para crear una."
        )
        return

    game = games[chat_id]

    if user.id in game["players"]:
        await update.message.reply_text(
            "😅 Ya estás dentro de la partida."
        )
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

    actualizar_actividad(chat_id)

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
            "⏰ La partida estaba inactiva y fue cerrada."
        )
        return

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No hay ninguna partida activa."
        )
        return

    game = games[chat_id]

    if user.id not in game["players"]:
        await update.message.reply_text(
            "❌ No estás dentro de la partida."
        )
        return

    game["players"].remove(user.id)
    game["names"].pop(user.id, None)
    game["positions"].pop(user.id, None)

    if len(game["players"]) == 0:
        del games[chat_id]

        await update.message.reply_text(
            "🎲 La partida terminó y quedó liberada.\n\n"
            "Ya pueden crear otra con /parchis."
        )
        return

    if game["turn"] >= len(game["players"]):
        game["turn"] = 0

    actualizar_actividad(chat_id)

    await update.message.reply_text(
        f"🚪 {user.full_name} salió de la partida.\n"
        f"👥 Quedan {len(game['players'])} jugadores."
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
            "⏰ La partida estuvo demasiado tiempo sin actividad y fue cerrada.\n\n"
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

    # 🎲 DADO REAL DE TELEGRAM
    resultado = await update.message.reply_dice(emoji="🎲")
    dado = resultado.dice.value

    posicion_actual = game["positions"][user.id]
    nueva_posicion = posicion_actual + dado

    if nueva_posicion >= META:
        game["positions"][user.id] = META
        scores[user.id] = scores.get(
       user.id,
      {"name": user.full_name, "points": 0, "wins": 0}
)

        scores[user.id]["name"] = user.full_name
        scores[user.id]["points"] += 5
        scores[user.id]["wins"] += 1
        await update.message.reply_text(
            f"🏁 {user.full_name} llegó a la META.\n\n"
            "🏆🎉 ¡TENEMOS GANADOR!"
        )

        del games[chat_id]
        return

    game["positions"][user.id] = nueva_posicion
    actualizar_actividad(chat_id)

    await update.message.reply_text(
        f"🎲 {user.full_name} sacó un {dado}.\n"
        f"📍 Avanzás a la posición {nueva_posicion}."
    )

    game["turn"] = (game["turn"] + 1) % len(game["players"])
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
            "❌ No hay ninguna partida activa."
        )
        return

    game = games[chat_id]

    texto = "🎲 TABLERO 🎲\n\n"

    for jugador_id in game["players"]:
        nombre = game["names"][jugador_id]
        posicion = game["positions"][jugador_id]

        texto += f"👤 {nombre}\n"
        texto += f"📍 Posición: {posicion}/{META}\n\n"

    siguiente = game["players"][game["turn"]]
    nombre_siguiente = game["names"][siguiente]

    texto += f"👉 Turno: {nombre_siguiente}"

    actualizar_actividad(chat_id)

    await update.message.reply_text(texto)


def main():
    if not TOKEN:
        raise ValueError(
            "No se encontró la variable TELEGRAM_TOKEN."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("parchis", parchis))
    app.add_handler(CommandHandler("unirme", unirme))
    app.add_handler(CommandHandler("salir", salir))
    app.add_handler(CommandHandler("tirar", tirar))
    app.add_handler(CommandHandler("tablero", tablero))
    app.add_handler(CommandHandler("reiniciar", reiniciar))
    app.add_handler(CommandHandler("cancelar", reiniciar))

    print("🎲 Bot de Parchís iniciado correctamente.")

    app.run_polling()


if __name__ == "__main__":
    main()
