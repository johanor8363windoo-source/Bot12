import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

def esta_bloqueado(user_id):
    cursor.execute("SELECT * FROM bloqueados WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

TOKEN = "8772649505:AAG3pptt_kbSHJ5KTB6LYAYr-MZ0s2_C0IU"
ADMINS = [7249440138]

app = ApplicationBuilder().token(TOKEN).build()

# 🧠 BASE DE DATOS
conn = sqlite3.connect("autos.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS autos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT,
    foto TEXT,
    precio TEXT,
    fotos_extra TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS uno (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT,
    foto TEXT,
    precio TEXT,
    fotos_extra TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS cuentas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT,
    video TEXT,
    precio TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bloqueados (
    user_id INTEGER PRIMARY KEY
)
""")

try:
    cursor.execute("ALTER TABLE autos ADD COLUMN fotos_extra TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE uno ADD COLUMN fotos_extra TEXT")
except:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    user_id INTEGER PRIMARY KEY,
    nombre TEXT,
    compras INTEGER DEFAULT 0,
    ultimo_uso TEXT,
    bloqueos INTEGER DEFAULT 0
)
""")
conn.commit()

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    nombre = user.first_name if user else "Usuario"

    if esta_bloqueado(user_id):
        if update.message:
            await update.message.reply_text("🚫 Has sido bloqueado del bot")
        else:
            await update.callback_query.message.reply_text("🚫 Has sido bloqueado del bot")
        return

    # 📅 fecha actual
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    # 🔎 verificar usuario
    cursor.execute("SELECT * FROM usuarios WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if data:
        cursor.execute("""
        UPDATE usuarios 
        SET nombre=?, ultimo_uso=? 
        WHERE user_id=?
        """, (nombre, fecha, user_id))
    else:
        cursor.execute("""
        INSERT INTO usuarios (user_id, nombre, ultimo_uso)
        VALUES (?, ?, ?)
        """, (user_id, nombre, fecha))

    conn.commit()

    # 📊 obtener stats
    cursor.execute("SELECT compras, ultimo_uso, bloqueos FROM usuarios WHERE user_id=?", (user_id,))
    stats = cursor.fetchone()

    compras = stats[0] if stats else 0
    ultimo_uso = stats[1] if stats else "Primera vez"
    bloqueos = stats[2] if stats else 0

    # 🎨 mensaje corto bonito
    texto = f"""

🔥 Bienvenido {nombre}

Los datos de tu usuario son:

🆔 <code>{user_id}</code>
🛒 Compras: {compras}
⏱ Último uso: {ultimo_uso}
🚫 Bloqueos: {bloqueos}

👇 Elige una opción
"""

    keyboard = [
        [InlineKeyboardButton("🚗 Ver autos", callback_data="ver_autos"),
        InlineKeyboardButton("👤 Ver cuentas", callback_data="ver_cuentas")],
        [InlineKeyboardButton("💠 Ver autos 1/1", callback_data="ver_uno")],
    ]

    if user_id in ADMINS:
        keyboard.append([InlineKeyboardButton("Panel Admin 👑", callback_data="admin")])

    foto = "AgACAgEAAxkBAAICdGnoOQLOkLH7kgg8MflNDaYAAaNSDQACRQxrG4dgQEeE5Xso6TlN4wEAAwIAA3gAAzsE"

    if update.callback_query:
        await update.callback_query.message.reply_photo(
            photo=foto,
            caption=texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_photo(
            photo=foto,
            caption=texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
async def debug_foto(update, context):
    print(update.message.photo[-1].file_id)

app.add_handler(MessageHandler(filters.PHOTO, debug_foto))
# ================= AUTOS =================

async def ver_autos(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["paso"] = "ver_autos"

    keyboard = [
    [
        InlineKeyboardButton("🚗 Charger", callback_data="cat_charger"),
        InlineKeyboardButton("🔥 Challenger", callback_data="cat_demon"),
    ],
    [
        InlineKeyboardButton("⚡ SRT", callback_data="cat_srt"),
        InlineKeyboardButton("🚙 Durango", callback_data="cat_durango"),
    ],
    [
        InlineKeyboardButton("🦖 TRX", callback_data="cat_trx"),
        InlineKeyboardButton("💎 Chrysler 300", callback_data="cat_chysler"),
    ],
    [
        InlineKeyboardButton("🏜 Raptor", callback_data="cat_raptor"),
        InlineKeyboardButton("🌄 Cherokee", callback_data="cat_cheroke"),
    ],
    [
        InlineKeyboardButton("⬅️ Regresar al Menú", callback_data="menu")
    ],
]

    # 🔥 SI EL MENSAJE YA FUE BORRADO → CREA UNO NUEVO
    try:
        await query.message.edit_text(
            "Selecciona categoría:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.chat.send_message(
            "Selecciona categoría:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
async def mostrar_autos(update, context):
    query = update.callback_query
    await query.answer()

    categoria = query.data.split("_")[1]
    cursor.execute("SELECT * FROM autos WHERE categoria=?", (categoria,))
    autos = cursor.fetchall()

    if not autos:
        await query.message.edit_text("❌ No hay autos disponibles.")
        return

    context.user_data["autos"] = autos
    context.user_data["index"] = 0
    context.user_data["categoria_actual"] = categoria

    await enviar_auto(query, context)

async def enviar_auto(query, context):
    autos = context.user_data["autos"]
    i = context.user_data["index"]
    auto = autos[i]

    keyboard = [
    [InlineKeyboardButton("⬅️ Ver Anterior ", callback_data="prev"),
    InlineKeyboardButton("➡️ Ver Siguente", callback_data="next")],


    [InlineKeyboardButton("👁 Ver a detalle el auto", callback_data="detalle_auto")],


    [InlineKeyboardButton("🛒 Comprar", callback_data="comprar_auto"),
    InlineKeyboardButton("🔙 Menú", callback_data="menu")],
]

    await query.message.delete()

    await query.message.chat.send_photo(
        photo=auto[2],
        caption=f"💰 {auto[3]}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def navegar(update, context):
    query = update.callback_query
    await query.answer()

    autos = context.user_data["autos"]
    i = context.user_data["index"]

    if query.data == "next":
        i += 1
    else:
        i -= 1

    # 🚫 SI YA NO HAY MÁS
    if i >= len(autos) or i < 0:
        keyboard = [
            [InlineKeyboardButton("🔄 Ver de nuevo", callback_data="repetir_autos")],
            [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
        ]

        await query.message.delete()

        await query.message.chat.send_message(
    "📭 El catálogo ha terminado",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
        return

    context.user_data["index"] = i
    await enviar_auto(query, context)

# ================= CUENTAS =================

async def ver_cuentas(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["paso"] = "ver_cuentas"

    keyboard = [
        [InlineKeyboardButton("TikTok", callback_data="cuenta_tiktok")],
        [InlineKeyboardButton("Instagram", callback_data="cuenta_instagram")],
        [InlineKeyboardButton("⬅️ Atrás", callback_data="back"),
        InlineKeyboardButton("🏠 Menú", callback_data="menu")],
    ]

    try:
        await query.message.edit_text(
            "Selecciona tipo:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.chat.send_message(
            "Selecciona tipo:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
async def mostrar_cuentas(update, context):
    query = update.callback_query
    await query.answer()

    categoria = query.data.split("_")[1]
    cursor.execute("SELECT * FROM cuentas WHERE categoria=?", (categoria,))
    cuentas = cursor.fetchall()

    if not cuentas:
        await query.message.edit_text("❌ No hay cuentas")
        return

    context.user_data["cuentas"] = cuentas
    context.user_data["index_cuenta"] = 0

    await enviar_cuenta(query, context)

async def enviar_cuenta(query, context):
    cuentas = context.user_data["cuentas"]
    i = context.user_data["index_cuenta"]
    cuenta = cuentas[i]

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_cuenta"),
            InlineKeyboardButton("➡️", callback_data="next_cuenta"),
        ],
        [InlineKeyboardButton("🛒 Comprar", callback_data="comprar_cuenta")],
        [InlineKeyboardButton("🔙 Menú", callback_data="menu")],

        [InlineKeyboardButton("⬅️ Atrás", callback_data="back"),
        InlineKeyboardButton("🏠 Menú", callback_data="menu")],
    ]

    await query.message.delete()

    await query.message.chat.send_video(
        video=cuenta[2],
        caption=f"💰 {cuenta[3]}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def navegar_cuentas(update, context):
    query = update.callback_query
    await query.answer()

    cuentas = context.user_data["cuentas"]
    i = context.user_data["index_cuenta"]

    if query.data == "next_cuenta":
        i = (i + 1) % len(cuentas)
    else:
        i = (i - 1) % len(cuentas)

    context.user_data["index_cuenta"] = i
    await enviar_cuenta(query, context)
# ================= AUTOS1/1 =================
async def ver_uno(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["paso"] = "ver_uno"
    

    keyboard = [
        [InlineKeyboardButton("Exclusivos", callback_data="uno_exclusivo")],
        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")],
    ]

    try:
        await query.message.edit_text(
            "💎 1/1 disponibles:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.chat.send_message(
            "💎 1/1 disponibles:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
async def mostrar_uno(update, context):
    query = update.callback_query
    await query.answer()

    categoria = query.data.split("_")[1]  # ✅ PRIMERO ESTO

    cursor.execute("SELECT * FROM uno WHERE categoria=?", (categoria,))
    items = cursor.fetchall()

    if not items:
        await query.message.edit_text("❌ No hay 1/1")
        return

    # ✅ GUARDAR BIEN
    context.user_data["uno"] = items
    context.user_data["index_uno"] = 0
    context.user_data["categoria_uno"] = categoria

    await enviar_uno(query, context)

async def enviar_uno(query, context):
    items = context.user_data["uno"]
    i = context.user_data["index_uno"]
    item = items[i]

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_uno"),
            InlineKeyboardButton("➡️", callback_data="next_uno"),
        ],
        [InlineKeyboardButton("🛒 Comprar", callback_data="comprar_uno")],
        [InlineKeyboardButton("🔙 Menú", callback_data="menu")],

        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")],

        [InlineKeyboardButton("👁 Ver a detalle", callback_data="detalle_uno")],
    ]

    await query.message.delete()

    await query.message.chat.send_photo(
        photo=item[2],
        caption=f"💰 {item[3]}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def navegar_uno(update, context):
    query = update.callback_query
    await query.answer()

    items = context.user_data["uno"]
    i = context.user_data["index_uno"]

    if query.data == "next_uno":
        i += 1
    else:
        i -= 1

    if i >= len(items) or i < 0:
        keyboard = [
            [InlineKeyboardButton("🔄 Ver de nuevo", callback_data="repetir_uno")],
            [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
        ]

        await query.message.delete()

        await query.message.chat.send_message(
    "📭 El catálogo ha terminado",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
        return

    context.user_data["index_uno"] = i
    await enviar_uno(query, context)

async def add_uno(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["modo"] = "uno"

    keyboard = [
        [InlineKeyboardButton("Exclusivo", callback_data="adduno_exclusivo")],
    ]

    await query.message.edit_text("Categoría:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_uno_categoria(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["categoria"] = query.data.split("_")[1]
    await query.message.edit_text("📸 Envía foto")

async def confirmar_uno(update, context):
    query = update.callback_query
    await query.answer()

    fotos_extra = context.user_data.get("fotos_extra", [])
    fotos_extra_str = "|".join(fotos_extra)

    cursor.execute(
        "INSERT INTO uno (categoria, foto, precio, fotos_extra) VALUES (?, ?, ?, ?)",
        (
            context.user_data["categoria"],
            context.user_data["foto"],
            context.user_data["precio"],
            fotos_extra_str
        )
    )
    conn.commit()

    await query.message.edit_caption("✅ 1/1 agregado con detalles")
    context.user_data.clear()

async def admin_panel(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ Auto", callback_data="add_auto")],
        [InlineKeyboardButton("➕ Cuenta", callback_data="add_cuenta")],
        [InlineKeyboardButton("💎 Agregar 1/1", callback_data="add_uno")],
        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")],
        [InlineKeyboardButton("🔓 Desbloquear usuarios", callback_data="ver_bloqueados")],
    ]

    try:
        await query.message.edit_text(
            "⚙️ Panel Admin",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.chat.send_message(
            "⚙️ Panel Admin",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def ver_bloqueados(update, context):
    query = update.callback_query
    await query.answer()

    cursor.execute("SELECT user_id FROM bloqueados")
    usuarios = cursor.fetchall()

    if not usuarios:
        await query.message.edit_text("✅ No hay usuarios bloqueados")
        return

    keyboard = []

    for u in usuarios:
        user_id = u[0]
        keyboard.append([
            InlineKeyboardButton(f"🔓 {user_id}", callback_data=f"desbloquear_{user_id}")
        ])

    keyboard.append([InlineKeyboardButton("⬅️ Atrás", callback_data="admin")])

    await query.message.edit_text(
        "🚫 Usuarios bloqueados:\nSelecciona uno para desbloquear",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def desbloquear_usuario(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    cursor.execute("DELETE FROM bloqueados WHERE user_id=?", (user_id,))
    conn.commit()

    # ✅ aviso al admin
    await query.message.edit_text(f"✅ Usuario {user_id} desbloqueado")

    # 📩 aviso al usuario
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Has sido desbloqueado, ya puedes usar el bot nuevamente"
        )
    except:
        pass  # por si el usuario nunca inició el bot
# ===== AUTO =====

async def add_auto(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["modo"] = "auto"

    keyboard = [
        [InlineKeyboardButton("Charger", callback_data="addcat_charger")],
        [InlineKeyboardButton("Demon", callback_data="addcat_demon")],
        [InlineKeyboardButton("SRT", callback_data="addcat_srt")],
        [InlineKeyboardButton("DURANGO", callback_data="addcat_durango")],

        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")],
    ]

    await query.message.edit_text("Categoría:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_categoria(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["categoria"] = query.data.split("_")[1]
    await query.message.edit_text("📸 Envía foto")



async def recibir_precio_general(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    modo = context.user_data.get("modo")

    # 🚗 AUTOS
    if modo == "auto":
        if "foto" not in context.user_data:
            await update.message.reply_text("❌ Primero envía la foto")
            return

        context.user_data["precio"] = update.message.text

        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_auto")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],

            [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
            [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
        ]

        await update.message.reply_photo(
            photo=context.user_data["foto"],
            caption=f"💰 {context.user_data['precio']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 👤 CUENTAS
    elif modo == "cuenta":
        if "video" not in context.user_data:
            await update.message.reply_text("❌ Primero envía el video")
            return

        context.user_data["precio"] = update.message.text

        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_cuenta")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],

            [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
            [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
        ]

        await update.message.reply_video(
            video=context.user_data["video"],
            caption=f"💰 {context.user_data['precio']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif modo == "uno":
        if "foto" not in context.user_data:
            await update.message.reply_text("❌ Primero envía la foto")
            return

        context.user_data["precio"] = update.message.text

        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_uno")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],

            [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
            [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
        ]

        await update.message.reply_photo(
            photo=context.user_data["foto"],
            caption=f"💰 {context.user_data['precio']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
async def confirmar_auto(update, context):
    query = update.callback_query
    await query.answer()

    fotos_extra = context.user_data.get("fotos_extra", [])
    fotos_extra_str = "|".join(fotos_extra)

    cursor.execute(
        "INSERT INTO autos (categoria, foto, precio, fotos_extra) VALUES (?, ?, ?, ?)",
        (
            context.user_data["categoria"],
            context.user_data["foto"],
            context.user_data["precio"],
            fotos_extra_str
        )
    )
    conn.commit()

    await query.message.edit_caption("✅ Auto agregado con detalles")
    context.user_data.clear()
# ===== CUENTA =====

async def add_cuenta(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["modo"] = "cuenta"

    keyboard = [
        [InlineKeyboardButton("TikTok", callback_data="addcuenta_tiktok")],
        [InlineKeyboardButton("Instagram", callback_data="addcuenta_instagram")],

        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")],
    ]

    await query.message.edit_text("Categoría:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_cuenta_categoria(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["categoria"] = query.data.split("_")[1]
    await query.message.edit_text("🎥 Envía video")

async def recibir_video(update, context):
    if context.user_data.get("modo") != "cuenta":
        return

    context.user_data["video"] = update.message.video.file_id
    await update.message.reply_text("💰 Precio:")

async def recibir_precio_cuenta(update, context):
    if context.user_data.get("modo") != "cuenta":
        return

    context.user_data["precio"] = update.message.text

    keyboard = [
        [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_cuenta")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
    
        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")],
    ]

    await update.message.reply_video(
        video=context.user_data["video"],
        caption=f"💰 {context.user_data['precio']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirmar_cuenta(update, context):
    query = update.callback_query
    await query.answer()

    cursor.execute("INSERT INTO cuentas (categoria, video, precio) VALUES (?, ?, ?)",
                   (context.user_data["categoria"], context.user_data["video"], context.user_data["precio"]))
    conn.commit()

    await query.message.edit_caption("✅ Cuenta agregada")
    context.user_data.clear()

# ===== GENERAL =====

async def cancelar(update, context):
    query = update.callback_query
    await query.answer()
    await query.message.edit_caption("❌ Cancelado")
    context.user_data.clear()

async def menu(update, context):
    await start(update, context)


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    paso = context.user_data.get("paso")

    await query.message.delete()

    if paso == "ver_autos":
        await ver_autos(update, context)

    elif paso == "ver_cuentas":
        await ver_cuentas(update, context)

    elif paso == "ver_uno":
        await ver_uno(update, context)

    else:
        # 👇 en vez de start()
        await menu(update, context)

# ================= SISTEMA DE PAGOS =================
async def comprar_auto(update, context):
    query = update.callback_query
    await query.answer()

    autos = context.user_data.get("autos")
    i = context.user_data.get("index")

    if not autos:
        return

    auto = autos[i]

    context.user_data["compra"] = {
        "tipo": "auto",
        "categoria": auto[1],
        "foto": auto[2],
        "precio": auto[3]
    }

    texto = f"""
🚗 Estás comprando:

📂 Categoría: {auto[1]}
💰 Precio: {auto[3]}

💳 Métodos de pago:
- OXXO
- Transferencia
- Binance

💸 Total a pagar: {auto[3]}
"""

    keyboard = [
        [InlineKeyboardButton("💰 Pagar", callback_data="pagar")],
        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")]
    ]

    await query.message.reply_photo(
        photo=auto[2],
        caption=texto,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def comprar_uno(update, context):
    query = update.callback_query
    await query.answer()

    items = context.user_data.get("uno")
    i = context.user_data.get("index_uno")

    if not items:
        return

    item = items[i]

    context.user_data["compra"] = {
        "tipo": "1/1",
        "categoria": item[1],
        "foto": item[2],
        "precio": item[3]
    }

    texto = f"""
💎 Estás comprando un 1/1:

📂 Categoría: {item[1]}
💰 Precio: {item[3]}

💳 Métodos de pago:
- OXXO
- Transferencia
- Binance

💸 Total a pagar: {item[3]}
"""

    keyboard = [
        [InlineKeyboardButton("💰 Pagar", callback_data="pagar")],
        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")]
    ]

    await query.message.reply_photo(
        photo=item[2],
        caption=texto,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def pagar(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["esperando_comprobante"] = True

    await query.message.reply_text(
        "📸 Envía tu comprobante de pago aquí."
    )

async def aceptar_pago(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("💬 Hablar con admin", url=f"https://t.me/{context.bot.username}")]
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text="✅ Tu pago ha sido aceptado",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await query.message.reply_text("✅ Pago confirmado al usuario")
    cursor.execute("""
    UPDATE usuarios 
    SET compras = compras + 1 
    WHERE user_id=?
    """, (user_id,))
    conn.commit()
async def recibir_foto(update, context):

    foto = update.message.photo[-1].file_id

    # ================= COMPROBANTE =================
    if context.user_data.get("esperando_comprobante"):
        user = update.effective_user
        compra = context.user_data.get("compra")

        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        texto = f"""
📥 NUEVO COMPROBANTE

👤 Usuario: {user.first_name}
🆔 ID: {user.id}

📦 Producto: {compra['tipo']}
📂 Categoría: {compra['categoria']}
💰 Precio: {compra['precio']}

🕒 Fecha: {fecha}
"""

        keyboard = [
            [InlineKeyboardButton("✅ Aceptar pago", callback_data=f"aceptar_{user.id}")],
            [InlineKeyboardButton("🚫 Bloquear", callback_data=f"bloquear_{user.id}")]
        ]

        for admin in ADMINS:
            await context.bot.send_photo(chat_id=admin, photo=foto, caption=texto)

            if compra["tipo"] == "cuenta":
                await context.bot.send_video(
                    chat_id=admin,
                    video=compra["foto"],
                    caption=f"🎬 Producto comprado\n💰 {compra['precio']}"
                )
            else:
                await context.bot.send_photo(
                    chat_id=admin,
                    photo=compra["foto"],
                    caption=f"🚗 Producto comprado\n💰 {compra['precio']}"
                )

            await context.bot.send_message(
                chat_id=admin,
                text="¿Aceptar pago?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        await update.message.reply_text("✅ Comprobante enviado, espera confirmación.")
        context.user_data["esperando_comprobante"] = False
        return

    # ================= ADMIN AUTOS / 1/1 =================
    modo = context.user_data.get("modo")

    if modo not in ["auto", "uno"]:
        return

    # 📸 FOTO PRINCIPAL
    if "foto" not in context.user_data:
        context.user_data["foto"] = foto
        context.user_data["fotos_extra"] = []

        keyboard = [
            [InlineKeyboardButton("✅ Sí", callback_data="add_extra_si")],
            [InlineKeyboardButton("❌ No", callback_data="add_extra_no")]
        ]

        await update.message.reply_text(
            "¿Deseas agregar imágenes a detalle?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 📸 FOTOS EXTRA
    if context.user_data.get("agregando_extra"):

        if len(context.user_data["fotos_extra"]) >= 5:
            await update.message.reply_text("❌ Máximo 5 fotos alcanzado")
            return

        context.user_data["fotos_extra"].append(foto)

        keyboard = [
            [InlineKeyboardButton("➕ Agregar otra", callback_data="add_extra_si")],
            [InlineKeyboardButton("✅ Terminar", callback_data="add_extra_no")]
        ]

        await update.message.reply_text(
            f"📸 Foto {len(context.user_data['fotos_extra'])} guardada",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

async def bloquear_usuario(update, context):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    cursor.execute("INSERT OR IGNORE INTO bloqueados (user_id) VALUES (?)", (user_id,))
    
    await query.message.reply_text(f"🚫 Usuario {user_id} bloqueado correctamente")
    cursor.execute("""
UPDATE usuarios 
SET bloqueos = bloqueos + 1 
WHERE user_id=?
""", (user_id,))
    conn.commit()
async def repetir_autos(update, context):
    query = update.callback_query
    await query.answer()

    categoria = context.user_data.get("categoria_actual")

    if not categoria:
        await query.message.reply_text("❌ Error, vuelve a seleccionar categoría")
        return

    cursor.execute("SELECT * FROM autos WHERE categoria=?", (categoria,))
    autos = cursor.fetchall()

    if not autos:
        await query.message.reply_text("❌ No hay autos")
        return

    context.user_data["autos"] = autos
    context.user_data["index"] = 0

    await enviar_auto(query, context)

async def repetir_uno(update, context):
    query = update.callback_query
    await query.answer()

    categoria = context.user_data.get("categoria_uno")

    if not categoria:
        await query.message.reply_text("❌ Error, vuelve a seleccionar categoría")
        return

    cursor.execute("SELECT * FROM uno WHERE categoria=?", (categoria,))
    items = cursor.fetchall()

    if not items:
        await query.message.reply_text("❌ No hay 1/1")
        return

    context.user_data["uno"] = items
    context.user_data["index_uno"] = 0

    await enviar_uno(query, context)

async def detalle_auto(update, context):
    query = update.callback_query
    await query.answer()

    autos = context.user_data.get("autos")
    i = context.user_data.get("index")

    auto = autos[i]

    fotos_extra = auto[4] if len(auto) > 4 else None

    if not fotos_extra:
        await query.message.reply_text("❌ No hay fotos de detalle")
        return

    fotos = fotos_extra.split("|")

    context.user_data["detalle_fotos"] = fotos
    context.user_data["detalle_index"] = 0
    context.user_data["precio_detalle"] = auto[3]

    await enviar_detalle(query, context)

async def detalle_uno(update, context):
    query = update.callback_query
    await query.answer()

    items = context.user_data.get("uno")
    i = context.user_data.get("index_uno")

    item = items[i]

    fotos_extra = item[4] if len(item) > 4 else None

    if not fotos_extra:
        await query.message.reply_text("❌ No hay fotos de detalle")
        return

    fotos = fotos_extra.split("|")

    context.user_data["detalle_fotos"] = fotos
    context.user_data["detalle_index"] = 0
    context.user_data["precio_detalle"] = item[3]

    await enviar_detalle(query, context)

async def enviar_detalle(query, context):
    fotos = context.user_data["detalle_fotos"]
    i = context.user_data["detalle_index"]
    precio = context.user_data["precio_detalle"]

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_detalle"),
            InlineKeyboardButton("➡️", callback_data="next_detalle"),
        ],
        [InlineKeyboardButton("🛒 Comprar", callback_data="comprar_auto")],
        [InlineKeyboardButton("🔙 Menú", callback_data="menu")],
    ]

    await query.message.delete()

    await query.message.chat.send_photo(
        photo=fotos[i],
        caption=f"💰 {precio}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def navegar_detalle(update, context):
    query = update.callback_query
    await query.answer()

    fotos = context.user_data["detalle_fotos"]
    i = context.user_data["detalle_index"]

    if query.data == "next_detalle":
        i = (i + 1) % len(fotos)
    else:
        i = (i - 1) % len(fotos)

    context.user_data["detalle_index"] = i

    await enviar_detalle(query, context)

async def extra_si(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["agregando_extra"] = True

    await query.message.reply_text("📸 Envía la foto")

async def extra_no(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["agregando_extra"] = False

    await query.message.reply_text("💰 Ahora envía el precio")
# ================= HANDLERS =================

app.add_handler(CommandHandler("start", start))

app.add_handler(CallbackQueryHandler(ver_autos, pattern="^ver_autos$"))
app.add_handler(CallbackQueryHandler(mostrar_autos, pattern="^cat_"))
app.add_handler(CallbackQueryHandler(navegar, pattern="^(prev|next)$"))
# 💎 1/1
app.add_handler(CallbackQueryHandler(ver_uno, pattern="^ver_uno$"))
app.add_handler(CallbackQueryHandler(mostrar_uno, pattern="^uno_"))
app.add_handler(CallbackQueryHandler(navegar_uno, pattern="^(prev_uno|next_uno)$"))
app.add_handler(CallbackQueryHandler(back, pattern="^back$"))

print("bot activo")

# 👑 ADMIN 1/1
app.add_handler(CallbackQueryHandler(add_uno, pattern="^add_uno$"))
app.add_handler(CallbackQueryHandler(set_uno_categoria, pattern="^adduno_"))
app.add_handler(CallbackQueryHandler(confirmar_uno, pattern="^confirmar_uno$"))
app.add_handler(CallbackQueryHandler(ver_cuentas, pattern="^ver_cuentas$"))
app.add_handler(CallbackQueryHandler(mostrar_cuentas, pattern="^cuenta_"))
app.add_handler(CallbackQueryHandler(navegar_cuentas, pattern="^(prev_cuenta|next_cuenta)$"))

app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin$"))
app.add_handler(CallbackQueryHandler(add_auto, pattern="^add_auto$"))
app.add_handler(CallbackQueryHandler(add_cuenta, pattern="^add_cuenta$"))

app.add_handler(CallbackQueryHandler(set_categoria, pattern="^addcat_"))
app.add_handler(CallbackQueryHandler(set_cuenta_categoria, pattern="^addcuenta_"))
app.add_handler(CallbackQueryHandler(comprar_auto, pattern="^comprar_auto$"))
app.add_handler(CallbackQueryHandler(comprar_uno, pattern="^comprar_uno$"))
app.add_handler(CallbackQueryHandler(pagar, pattern="^pagar$"))
app.add_handler(CallbackQueryHandler(aceptar_pago, pattern="^aceptar_"))
app.add_handler(CallbackQueryHandler(detalle_auto, pattern="^detalle_auto$"))
app.add_handler(CallbackQueryHandler(detalle_uno, pattern="^detalle_uno$"))

app.add_handler(CallbackQueryHandler(navegar_detalle, pattern="^(prev_detalle|next_detalle)$"))

app.add_handler(CallbackQueryHandler(extra_si, pattern="^add_extra_si$"))
app.add_handler(CallbackQueryHandler(extra_no, pattern="^add_extra_no$"))

app.add_handler(CallbackQueryHandler(confirmar_auto, pattern="^confirmar_auto$"))
app.add_handler(CallbackQueryHandler(confirmar_cuenta, pattern="^confirmar_cuenta$"))
app.add_handler(CallbackQueryHandler(bloquear_usuario, pattern="^bloquear_"))
app.add_handler(CallbackQueryHandler(cancelar, pattern="^cancelar$"))
app.add_handler(CallbackQueryHandler(ver_bloqueados, pattern="^ver_bloqueados$"))
app.add_handler(CallbackQueryHandler(desbloquear_usuario, pattern="^desbloquear_"))
app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(repetir_uno, pattern="^repetir_uno$"))
app.add_handler(CallbackQueryHandler(repetir_autos, pattern="^repetir_autos$"))

app.add_handler(MessageHandler(filters.PHOTO, recibir_foto))
app.add_handler(MessageHandler(filters.VIDEO, recibir_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_precio_general))

app.run_polling()