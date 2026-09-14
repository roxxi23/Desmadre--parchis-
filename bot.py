import os
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

games = {}

COLORES = ["🔴", "🔵", "🟢", "🟡"]


def crear_tablero(game):
    tablero = []

    for posicion in range(1, 69):
        fichas = ""

        for i, user_id in enumerate(game["players"]):
            if game["positions"][user_id] == posicion:
                fichas += COLORES[i]

        if fichas:
            tablero.append(f"{posicion:02d}{fichas}")
        else:
            tablero.append(f"{posicion:02d}⬜")

    filas = []

    for i in range(0, 68, 17):
        fila = tablero[i:i + 17]
        filas.append(" ".join(fila))

    texto = "🏆🎲 TABLERO DESMADRE PARCHÍS 🎲🏆\n\n"
    texto += "\n".join(filas)
    texto += "\n\n🏠 INICIO"

    for i, user_id in enumerate(game["players"]):
        nombre = game["names"][user_id]
        posicion = game["positions"][user_id]
        texto += f"\n{COLORES[i]} {nombre}: casilla {posicion}"

    texto += "\n\n🏁 META: 68"

    return texto


async def parchis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id in games:
        await update.message.reply_text(
            "🎲 Ya hay una partida creada.\n"
            "Usá /unirme para entrar."
        )
        return

    games[chat_id] = {
        "players": [user.id],
        "names": {user.id: user.full_name},
        "turn": 0,
        "positions": {user.id: 0},
        "started": False
    }

    await update.message.reply_text(
        "🎲❤️ ¡NUEVA PARTIDA DE DESMADRE PARCHÍS! ❤️🎲\n\n"
        f"👤 {user.full_name} creó la partida.\n\n"
        "👥 Los demás jugadores pueden entrar con /unirme\n"
        "🏆 De 2 a 4 jugadores.\n"
        "🎲 Cuando estén listos, usen /tirar"
    )


async def unirme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        await update.message.reply_text(
            "❌ Primero creá una partida con /parchis."
        )
        return

    game = games[chat_id]

    if user.id in game["players"]:
        await update.message.reply_text(
            "😄 Ya estás dentro de la partida."
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

    await update.message.reply_text(
        f"🎉 {user.full_name} se unió a la partida.\n\n"
        f"👥 Jugadores: {len(game['players'])}/4\n"
        "🎲 Ya pueden empezar con /tirar"
    )

    if len(game["players"]) == 4:
        await update.message.reply_text(
            "🔥 ¡PARTIDA COMPLETA! 🔥\n"
            "🎲 ¡Que empiece el desmadre!"
        )


async def salir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No hay una partida activa."
        )
        return

    game = games[chat_id]

    if user.id not in game["players"]:
        await update.message.reply_text(
            "❌ No estás dentro de la partida."
        )
        return

    indice = game["players"].index(user.id)

    game["players"].remove(user.id)
    del game["names"][user.id]
    del game["positions"][user.id]

    if len(game["players"]) == 0:
        del games[chat_id]
        await update.message.reply_text(
            "🎲 La partida terminó porque no quedan jugadores."
        )
        return

    if indice <= game["turn"]:
        game["turn"] = max(0, game["turn"] - 1)

    game["turn"] %= len(game["players"])

    await update.message.reply_text(
        f"👋 {user.full_name} salió de la partida."
    )


async def tirar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games:
        await update.message.reply_text(
            "❌ Primero creá una partida con /parchis."
        )
        return

    game = games[chat_id]

    if len(game["players"]) < 2:
        await update.message.reply_text(
            "👥 Necesitamos al menos 2 jugadores.\n"
            "Usá /unirme para entrar."
        )
        return

    current_player = game["players"][game["turn"]]

    if user.id != current_player:
        nombre = game["names"][current_player]
        await update.message.reply_text(
            f"⏳ Todavía no te toca.\n"
            f"🎲 Es el turno de {nombre}."
        )
        return

    dado = random.randint(1, 6)

    nueva_posicion = game["positions"][user.id] + dado

    if nueva_posicion > 68:
        nueva_posicion = 68

    game["positions"][user.id] = nueva_posicion

    await update.message.reply_text(
        f"🎲 {user.full_name} tiró el dado...\n\n"
        f"🎲 ¡Salió un {dado}!\n"
        f"📍 Avanzás a la casilla {nueva_posicion}."
    )

    await update.message.reply_text(crear_tablero(game))

    if nueva_posicion >= 68:
        await update.message.reply_text(
            f"🏆🎉 ¡TENEMOS GANADOR! 🎉🏆\n\n"
            f"👑 {user.full_name} llegó a la META.\n"
            f"🎲 ¡Ganaste Desmadre Parchís!"
        )

        del games[chat_id]
        return

    game["turn"] = (game["turn"] + 1) % len(game["players"])

    siguiente = game["players"][game["turn"]]
    nombre_siguiente = game["names"][siguiente]

    await update.message.reply_text(
        f"👉 Ahora le toca a {nombre_siguiente}.\n"
        "🎲 Usá /tirar"
    )


async def tablero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No hay una partida activa."
        )
        return

    game = games[chat_id]

    await update.message.reply_text(
        crear_tablero(game)
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲❤️ DESMADRE PARCHÍS ❤️🎲\n\n"
        "/parchis — Crear una partida\n"
        "/unirme — Unirme a la partida\n"
        "/salir — Salir de la partida\n"
        "/tirar — Tirar el dado\n"
        "/tablero — Ver el tablero\n"
        "/ayuda — Ver los comandos\n\n"
        "👥 De 2 a 4 jugadores\n"
        "🏁 La meta está en la casilla 68\n"
        "🔥 ¡Que empiece el desmadre!"
    )


def main():
    token = os.environ["TELEGRAM_TOKEN"]

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("parchis", parchis))
    app.add_handler(CommandHandler("unirme", unirme))
    app.add_handler(CommandHandler("salir", salir))
    app.add_handler(CommandHandler("tirar", tirar))
    app.add_handler(CommandHandler("tablero", tablero))
    app.add_handler(CommandHandler("ayuda", ayuda))

    print("🎲 Desmadre Parchís está funcionando...")

    app.run_polling()


if __name__ == "__main__":
    main()
