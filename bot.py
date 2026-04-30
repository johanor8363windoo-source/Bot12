import sqlite3
import random
from datetime import datetime
from datetime import datetime, timedelta
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
ADMINS = [7957443258, 5665870463]
CANAL_REFERENCIAS = -5137021856  # 👈 cambia esto por tu canal o grupo

app = ApplicationBuilder().token(TOKEN).build()

# 🧠 BASE DE DATOS
conn = sqlite3.connect("autos.db", check_same_thread=False)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE comprobantes ADD COLUMN auto_id INTEGER")
except:
    pass
try:
    cursor.execute("ALTER TABLE cuentas ADD COLUMN correo TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE cuentas ADD COLUMN numero INTEGER")
except:
    pass
try:
    cursor.execute("ALTER TABLE comprobantes ADD COLUMN auto_id INTEGER")
    conn.commit()
    print("✅ Columna auto_id agregada")
except Exception as e:
    print("ℹ️ auto_id ya existe o no se pudo agregar:", e)
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
try:
    cursor.execute("ALTER TABLE autos ADD COLUMN correo TEXT")
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS comprobantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    nombre TEXT,
    producto TEXT,
    categoria TEXT,
    precio TEXT,
    foto_comprobante TEXT,
    foto_producto TEXT,
    fecha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS comprobantes_cuentas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    nombre TEXT,
    precio TEXT,
    foto TEXT,
    fecha TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT
)
""")

conn.commit()

MENSAJES_AUTOS = [
    "🔥 Auto a muy buen precio",
    "💎 Oferta exclusiva",
    "⚡ Aprovecha antes que se acaben",
    "🚗 Listo para entrega inmediata",
    "💰 Precio especial por tiempo limitado"
]

async def esta_en_grupo(context, user_id):
    try:
        miembro = await context.bot.get_chat_member(CANAL_REFERENCIAS, user_id)

        if miembro.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except:
        return False
# 🚀 START
from datetime import datetime, timedelta

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    # 🚫 SI ES GRUPO
    if update.effective_chat.type != "private":
        nombre = user.first_name if user else "Usuario"

        await update.message.reply_text(
            f"{nombre} Escríbeme por priv, aquí me da Penita 🥺"
        )
        return

    user_id = user.id
    nombre = user.first_name if user else "Usuario"
    username = f"@{user.username}" if user.username else "Sin username"

    # 🚫 bloqueado
    if esta_bloqueado(user_id):
        await update.message.reply_text(
            "🚫 Has sido bloqueado permanentemente del bot, contacta al administrador."
        )
        return

    # 📅 fecha actual
    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y %H:%M")

    # 🔎 buscar usuario
    cursor.execute("SELECT ultimo_uso FROM usuarios WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    # 🔄 obtener reset
    cursor.execute("SELECT valor FROM config WHERE clave='ultimo_reset'")
    reset_data = cursor.fetchone()

    reset_fecha = None
    if reset_data:
        try:
            reset_fecha = datetime.strptime(reset_data[0], "%d/%m/%Y %H:%M")
        except:
            pass

    # 🔥 detectar si es "nuevo"
    es_nuevo = False

    if data is None:
        es_nuevo = True
    else:
        try:
            ultima_fecha = datetime.strptime(data[0], "%d/%m/%Y %H:%M")

            if reset_fecha and ultima_fecha < reset_fecha:
                es_nuevo = True

            elif ahora - ultima_fecha >= timedelta(days=3):
                es_nuevo = True

        except:
            es_nuevo = True

    # 📸 obtener foto perfil
    foto_perfil = None
    try:
        perfil = await context.bot.get_user_profile_photos(user_id)
        if perfil.total_count > 0:
            foto_perfil = perfil.photos[0][-1].file_id
    except:
        pass

    # 🔔 AVISO AL ADMIN
    if es_nuevo:
        texto_admin = f"""
🚀 Usuario interactuó con /start

👤 Nombre: {nombre}
📛 Usuario: {username}
🆔 ID: {user_id}
🕒 {fecha}
📩 Comando: /start
"""

        for admin in ADMINS:
            try:
                if foto_perfil:
                    await context.bot.send_photo(
                        chat_id=admin,
                        photo=foto_perfil,
                        caption=texto_admin
                    )
                else:
                    await context.bot.send_message(
                        chat_id=admin,
                        text=texto_admin
                    )
            except Exception as e:
                print("Error admin:", e)

    # 💾 guardar usuario
    if data is None:
        cursor.execute("""
        INSERT INTO usuarios (user_id, nombre, ultimo_uso)
        VALUES (?, ?, ?)
        """, (user_id, nombre, fecha))
    else:
        cursor.execute("""
        UPDATE usuarios 
        SET nombre=?, ultimo_uso=? 
        WHERE user_id=?
        """, (nombre, fecha, user_id))

    conn.commit()

    # =========================
    # 📊 STATS
    # =========================
    cursor.execute("SELECT compras, ultimo_uso, bloqueos FROM usuarios WHERE user_id=?", (user_id,))
    stats = cursor.fetchone()

    compras = stats[0] if stats else 0
    ultimo_uso = stats[1] if stats else "Primera vez"
    bloqueos = stats[2] if stats else 0

    en_grupo = await esta_en_grupo(context, user_id)
    estado_grupo = "✅ Sí" if en_grupo else "❌ No"

    # =========================
    # 🎛 BOTONES (USA LOS TUYOS)
    # =========================
    keyboard = [
        [InlineKeyboardButton("🚗 Ver autos", callback_data="ver_autos"),
         InlineKeyboardButton("👤 Ver cuentas", callback_data="ver_cuentas")],
        [InlineKeyboardButton("💠 Ver autos 1/1", callback_data="ver_uno")],
        [InlineKeyboardButton("👥 Unirse al grupo", url="https://t.me/+-PsaEDkVkckyOWM5")],
        [InlineKeyboardButton("⭐ Reseña", callback_data="reseña")],
        [InlineKeyboardButton("📦 Mis compras", callback_data="mis_compras")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="informacion")]
    ]

    if user_id in ADMINS:
        keyboard.append([InlineKeyboardButton("👑 Panel Admin", callback_data="admin")])
        

    # 📸 FOTO MENU (tu file_id)
    foto_menu = "AgACAgEAAxkBAAICdGnoOQLOkLH7kgg8MflNDaYAAaNSDQACRQxrG4dgQEeE5Xso6TlN4wEAAwIAA3gAAzsE"

    # =========================
    # 👑 ADMIN
    # =========================
    if user_id in ADMINS:

        texto_admin = f"""
👑 <b>Bienvenido Admin {nombre}</b>

🆔 <code>{user_id}</code>
"""

        stats_admin = f"""
📊 <b>Estadísticas</b>

🛒 Compras: {compras}
⏱ Último uso: {ultimo_uso}
🚫 Bloqueos: {bloqueos}
👥 En el grupo: {estado_grupo}
"""

        # 1️⃣ Bienvenida
        await update.message.reply_text(
            texto_admin,
            parse_mode="HTML"
        )

        # 2️⃣ Stats + menú
        await update.message.reply_photo(
            photo=foto_menu,
            caption=stats_admin + "\n\n👇 Elige una opción",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    # =========================
    # 👤 USUARIO NORMAL
    # =========================
    else:

        texto = f"""
Hola {nombre}

🆔 <code>{user_id}</code>
🛒 Compras: {compras}
⏱ Último uso: {ultimo_uso}
🚫 Bloqueos: {bloqueos}
👥 En el grupo: {estado_grupo}

👇 Elige una opción
"""

        await update.message.reply_photo(
            photo=foto_menu,
            caption=texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
async def imforma_cion(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
    ]

    # 🧹 borrar menú anterior
    try:
        await query.message.delete()
    except:
        pass

    # 📩 enviar mensaje
    await query.message.chat.send_message(
        text="""
ℹ️ Información del bot

Este bot te permite:
🚗 Ver autos disponibles
👤 Ver cuentas
⭐ Enviar reseñas
📦 Ver tus compras

🔥 Más funciones próximamente
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
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
        InlineKeyboardButton("⚡Raptor ", callback_data="cat_srt"),
        InlineKeyboardButton("🚙 Durango", callback_data="cat_durango"),
    ],
    [
        InlineKeyboardButton("🦖 TRX", callback_data="cat_trx"),
        InlineKeyboardButton("🦖 Ram 1500", callback_data="cat_1500"),
    ],
    [
        
        InlineKeyboardButton("🌄 Cherokee", callback_data="cat_cheroke"),
    ]
]

# ✅ AGREGAS BOTÓN EXTRA BIEN
    keyboard.append([InlineKeyboardButton("🏎 Deportivos", callback_data="deportivos")])

# ✅ BOTÓN FINAL
    keyboard.append([InlineKeyboardButton("⬅️ Regresar al Menú", callback_data="menu")])
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

async def ver_deportivos(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("GT3", callback_data="cat_gt3")],
        [InlineKeyboardButton("R8", callback_data="cat_r8")],
        [InlineKeyboardButton("GTR R35", callback_data="cat_gtr_r35")],
        [InlineKeyboardButton("Corvette C8", callback_data="cat_corvette_c8")],

        [InlineKeyboardButton("⬅️ Atrás", callback_data="ver_autos")]
    ]

    await query.message.edit_text(
        "🏎 Categorías Deportivos",
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

    mensaje_random = random.choice(MENSAJES_AUTOS)

    nombre = auto[1]      # 👈 modelo
    foto = auto[2]
    precio = auto[3]
    info = auto[5] if len(auto) > 5 else ""

    texto = f"""
🚗 {nombre}
💰 {precio}
{mensaje_random}
📝 Todos son 414 o 300 hp
"""

    keyboard = [
        [
            InlineKeyboardButton("⬅️ Ver Anterior", callback_data="prev"),
            InlineKeyboardButton("➡️ Ver Siguiente", callback_data="next")
        ],
        [InlineKeyboardButton("👁 Ver a detalle el auto", callback_data="detalle_auto")],
        [
            InlineKeyboardButton("🛒 Comprar auto", callback_data="comprar_auto"),
            InlineKeyboardButton("🔙 Menú", callback_data="menu")
        ],
    ]

    if query.from_user.id in ADMINS:
        keyboard.append([
            InlineKeyboardButton("🗑 Borrar este auto", callback_data=f"borrar_auto_{auto[0]}")
        ])

    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_photo(
        photo=foto,
        caption=texto,
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
        [
            InlineKeyboardButton("💰 40 MX", callback_data="cuenta_40"),
            InlineKeyboardButton("💰 60 MX", callback_data="cuenta_60"),
        ],
        [
            InlineKeyboardButton("💰 80 MX", callback_data="cuenta_80"),
            InlineKeyboardButton("💰 100 MX", callback_data="cuenta_100"),
        ],
        [
            InlineKeyboardButton("💰 120 MX", callback_data="cuenta_120"),
            InlineKeyboardButton("💰 140 MX", callback_data="cuenta_140"),
        ],
        [
            InlineKeyboardButton("💰 160 MX", callback_data="cuenta_160"),
            InlineKeyboardButton("💰 180 MX", callback_data="cuenta_180"),
        ],
        [
            InlineKeyboardButton("💰 200 MX", callback_data="cuenta_200"),
            InlineKeyboardButton("💰 250 MX", callback_data="cuenta_250"),
        ],
        [
            InlineKeyboardButton("⬅️ Atrás", callback_data="back"),
            InlineKeyboardButton("🏠 Menú", callback_data="menu"),
        ],
    ]

    try:
        await query.message.edit_text(
            "💳 Selecciona el precio de la cuenta:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.chat.send_message(
            "💳 Selecciona el precio de la cuenta:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
async def mostrar_cuentas(update, context):
    query = update.callback_query

    try:
        await query.answer()
    except:
        pass

    categoria = query.data.split("_")[1]

    cursor.execute("SELECT * FROM cuentas WHERE categoria=?", (categoria,))
    cuentas = cursor.fetchall()

    if not cuentas:
        try:
            await query.message.edit_text("❌ No hay cuentas")
        except:
            await query.message.chat.send_message("❌ No hay cuentas")
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
    ]

    try:
        await query.message.delete()
    except:
        pass

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

    cursor.execute("SELECT * FROM uno ORDER BY id DESC")
    items = cursor.fetchall()

    if not items:
        try:
            await query.message.edit_text("❌ No hay autos 1/1 disponibles")
        except:
            await query.message.delete()
            await query.message.chat.send_message("❌ No hay autos 1/1 disponibles")
        return  # 🔥 IMPORTANTE

    # ✅ SOLO SI SÍ HAY AUTOS
    context.user_data["uno"] = items
    context.user_data["index_uno"] = 0

    await enviar_uno(query, context)
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
    [InlineKeyboardButton("👁 Ver a detalle", callback_data="detalle_uno")],
    [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
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

    [
        InlineKeyboardButton("➕ Auto", callback_data="add_auto"),
        InlineKeyboardButton("💎 1/1", callback_data="add_uno")
    ],

    [
        InlineKeyboardButton("➕ Cuenta", callback_data="add_cuenta")
    ],

    [
        InlineKeyboardButton("📥 Comprobantes", callback_data="ver_comprobantes"),
        InlineKeyboardButton("📥 Cuentas", callback_data="ver_comprobantes_cuentas")
    ],

    [
        InlineKeyboardButton("🗑 Comprobantes", callback_data="borrar_comprobantes"),
        InlineKeyboardButton("🗑 Autos", callback_data="borrar_todos_autos")
    ],

    [
        InlineKeyboardButton("🔓 Usuarios", callback_data="ver_bloqueados"),
        InlineKeyboardButton("📊 Estadísticas", callback_data="stats")
    ],

    [
        InlineKeyboardButton("⭐ Ver reseñas", callback_data="ver_reseñas"),
        InlineKeyboardButton("📢 Enviar anuncio", callback_data="broadcast")
    ],

    [
        InlineKeyboardButton("🔄 Reiniciar conteo", callback_data="resetear")
    ],

    [
        InlineKeyboardButton("⬅️ Atrás", callback_data="back"),
        InlineKeyboardButton("🏠 Menú", callback_data="menu")
    ],
    [
       InlineKeyboardButton("💰 Precio global autos", callback_data="set_precio_global")
    ],
]
    try:
        await query.message.edit_text(
            text="""
➕ Auto → Usa este botón para agregar un auto nuevo al sistema 🚗  

💎 1/1 → Agrega un auto exclusivo (solo habrá uno disponible)  

➕ Cuenta → Sirve para registrar una nueva cuenta 👤  

📥 Comprobantes → Aquí revisas los comprobantes enviados de autos  

🔓 Usuarios → Permite desbloquear usuarios bloqueados  

🗑 Comprob. → Borra TODOS los comprobantes (no se pueden recuperar) ⚠️  

🗑 Autos → Elimina todos los autos normales (no afecta los exclusivos)  

📥 Cuentas → Revisa comprobantes de pago de cuentas  

↩️ Atrás → Regresa a la pantalla anterior  
🏠 Menú → Vuelve al menú principal""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.chat.send_message(
            text="""
➕ Auto → Usa este botón para agregar un auto nuevo al sistema 🚗  

💎 1/1 → Agrega un auto exclusivo (solo habrá uno disponible)  

➕ Cuenta → Sirve para registrar una nueva cuenta 👤  

📥 Comprobantes → Aquí revisas los comprobantes enviados de autos  

🔓 Usuarios → Permite desbloquear usuarios bloqueados  

🗑 Comprob. → Borra TODOS los comprobantes (no se pueden recuperar) ⚠️  

🗑 Autos → Elimina todos los autos normales (no afecta los exclusivos)  

📥 Cuentas → Revisa comprobantes de pago de cuentas  

↩️ Atrás → Regresa a la pantalla anterior  
🏠 Menú → Vuelve al menú principal""",
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
async def add_auto(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["modo"] = "auto"

    keyboard = [
        [
            InlineKeyboardButton("🚗 Charger", callback_data="addcat_charger"),
            InlineKeyboardButton("🔥 Challenger", callback_data="addcat_demon"),
        ],
        [
            InlineKeyboardButton("⚡ Raptor", callback_data="addcat_raptor"),
            InlineKeyboardButton("🚙 Durango", callback_data="addcat_durango"),
        ],
        [
            InlineKeyboardButton("🦖 TRX", callback_data="addcat_trx"),
            InlineKeyboardButton("🚙 RAM 1500", callback_data="addcat_1500"),
        ],
        [
            InlineKeyboardButton("🌄 Cherokee", callback_data="addcat_cheroke"),
        ],
        # 🔥 DEPORTIVOS
        [
            InlineKeyboardButton("GT3", callback_data="addcat_gt3"),
            InlineKeyboardButton("R8", callback_data="addcat_r8"),
        ],
        [
            InlineKeyboardButton("GTR R35", callback_data="addcat_gtr_r35"),
            InlineKeyboardButton("Corvette C8", callback_data="addcat_corvette_c8"),
        ],
        [
            InlineKeyboardButton("⬅️ Volver", callback_data="admin")
        ]
    ]

    # 🔥 SOLUCIÓN PRO (SIN ERRORES)
    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_message(
        "📂 Selecciona categoría:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_categoria(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["categoria"] = query.data.split("_")[1]

    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_message("📸 Envía foto del auto")

async def recibir_precio_general(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # ⭐ RESEÑAS (PRIORIDAD MÁXIMA)
    if context.user_data.get("modo_reseña"):
        user = update.effective_user
        texto = update.message.text
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        cursor.execute("""
        INSERT INTO reseñas (user_id, nombre, mensaje, fecha)
        VALUES (?, ?, ?, ?)
        """, (user.id, user.first_name, texto, fecha))

        conn.commit()

        await update.message.reply_text("✅ Gracias por tu reseña ⭐")

        # 📢 OPCIONAL: mandar a canal
        try:
            await context.bot.send_message(
                chat_id=CANAL_REFERENCIAS,
                text=f"""
⭐ <b>Nueva reseña</b>

👤 {user.first_name}
💬 El texto solo lo puede ver el admin
🕒 {fecha}
""",
                parse_mode="HTML"
            )
        except:
            pass

        context.user_data["modo_reseña"] = False
        return

    # 🚫 SOLO ADMIN DESPUÉS DE ESTO
    if update.effective_user.id not in ADMINS:
        return
    # 📧 GUARDAR CORREO
    if context.user_data.get("esperando_correo"):
        context.user_data["correo"] = update.message.text
        context.user_data["esperando_correo"] = False

        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_auto")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
        ]

        await update.message.reply_photo(
            photo=context.user_data["foto"],
            caption=f"💰 {context.user_data['precio']}\n📧 {context.user_data['correo']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    modo = context.user_data.get("modo")

    # 🚗 AUTOS
    if modo == "auto":
        if "foto" not in context.user_data:
            await update.message.reply_text("❌ Primero envía la foto")
            return

        context.user_data["precio"] = update.message.text

        await update.message.reply_text("📧 Ahora envía el correo donde está el auto")
        context.user_data["esperando_correo"] = True
        return

    # 👤 CUENTAS
    # 📧 CORREO CUENTA
    if context.user_data.get("esperando_correo_cuenta"):
        context.user_data["correo"] = update.message.text
        context.user_data["esperando_correo_cuenta"] = False

        await update.message.reply_text("💰 Ahora envía el precio")
        context.user_data["esperando_precio_cuenta"] = True
        return


# 💰 PRECIO CUENTA
    if context.user_data.get("esperando_precio_cuenta"):
        context.user_data["precio"] = update.message.text
        context.user_data["esperando_precio_cuenta"] = False

        keyboard = [
        [InlineKeyboardButton("✅ Agregar", callback_data="confirmar_cuenta")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]

        await update.message.reply_video(
            video=context.user_data["video"],
            caption=f"""
    👤 Cuenta #{context.user_data.get("numero", "?")}

    💰 {context.user_data['precio']}
    📧 {context.user_data['correo']}
    """,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
async def confirmar_auto(update, context):
    query = update.callback_query
    await query.answer()

    fotos_extra = context.user_data.get("fotos_extra", [])
    fotos_extra_str = "|".join(fotos_extra)

    cursor.execute(
        "INSERT INTO autos (categoria, foto, precio, fotos_extra, correo) VALUES (?, ?, ?, ?, ?)",
        (
            context.user_data["categoria"],
            context.user_data["foto"],
            context.user_data["precio"],
            fotos_extra_str,
            context.user_data["correo"]
        )
    )
    conn.commit()

    # 🔘 BOTONES
    keyboard = [
        [InlineKeyboardButton("➕ Agregar otro auto", callback_data="add_auto")],
        [InlineKeyboardButton("🏠 Panel admin", callback_data="admin")]
    ]

    await query.message.edit_caption(
        caption="✅ Auto agregado con detalles",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.user_data.clear()

async def safe_send(query, text, keyboard=None, photo=None):
    try:
        await query.message.delete()
    except:
        pass

    if photo:
        await query.message.chat.send_photo(
            photo=photo,
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
    else:
        await query.message.chat.send_message(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
# ===== CUENTA =====

async def add_cuenta(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["modo"] = "cuenta"

    keyboard = [
        [
            InlineKeyboardButton("💰 40 MX", callback_data="addcuenta_40"),
            InlineKeyboardButton("💰 60 MX", callback_data="addcuenta_60"),
        ],
        [
            InlineKeyboardButton("💰 80 MX", callback_data="addcuenta_80"),
            InlineKeyboardButton("💰 100 MX", callback_data="addcuenta_100"),
        ],
        [
            InlineKeyboardButton("💰 120 MX", callback_data="addcuenta_120"),
            InlineKeyboardButton("💰 140 MX", callback_data="addcuenta_140"),
        ],
        [
            InlineKeyboardButton("💰 160 MX", callback_data="addcuenta_160"),
            InlineKeyboardButton("💰 180 MX", callback_data="addcuenta_180"),
        ],
        [
            InlineKeyboardButton("💰 200 MX", callback_data="addcuenta_200"),
            InlineKeyboardButton("💰 250 MX", callback_data="addcuenta_250"),
        ],

        # 🔙 navegación
        [
            InlineKeyboardButton("⬅️ Atrás", callback_data="back"),
            InlineKeyboardButton("🏠 Menú", callback_data="menu"),
        ],
    ]
    
    await query.message.edit_text(
        "💳 Selecciona el precio de la cuenta:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
    await update.message.reply_text("📧 Envía el correo de la cuenta")
    context.user_data["esperando_correo_cuenta"] = True

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
    "auto_id": auto[0],  # 🔥 CLAVE
    "categoria": auto[1],
    "foto": auto[2],
    "precio": auto[3]
}

    texto = f"""
🚗 Estás comprando:

📂 Categoría: {auto[1]}
💰 Precio: {auto[3]}

💸 MÉTODOS DE PAGO DISPONIBLES 💸  

━━━━━━━━━━━━━━━  
💳 Transferencia (Spin by Oxxo)  
👤 Nombre: Reyna Margarita Hernández  
🔢 7289 6900 0155 6615 39  

🏪 Depósito en Oxxo  
🔢 2242 1702 9026 6032  

━━━━━━━━━━━━━━━  

🌎 INTERNACIONAL  

💰 PayPal  
📩 albertoya@hotmail.com  

━━━━━━━━━━━━━━━  

⚡ Envía tu comprobante para confirmar tu pago

💸 Total a pagar: "{auto[3]}"
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

💸 MÉTODOS DE PAGO DISPONIBLES 💸  

━━━━━━━━━━━━━━━  
💳 Transferencia (Spin by Oxxo)  
👤 Nombre: Reyna Margarita Hernández  
🔢 7289 6900 0155 6615 39  

🏪 Depósito en Oxxo  
🔢 2242 1702 9026 6032  

━━━━━━━━━━━━━━━  

🌎 INTERNACIONAL  

💰 PayPal  
📩 albertoya@hotmail.com  

━━━━━━━━━━━━━━━  

⚡ Envía tu comprobante para confirmar tu pago


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

    # ================= COMPROBANTE AUTOS =================
    if context.user_data.get("esperando_comprobante"):
        user = update.effective_user
        compra = context.user_data.get("compra")

        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        cursor.execute("""
        INSERT INTO comprobantes 
        (user_id, nombre, producto, categoria, precio, foto_comprobante, foto_producto, fecha, auto_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
    user.id,
    user.first_name,
    compra["tipo"],
    compra["categoria"],
    compra["precio"],
    foto,
    compra["foto"],
    fecha,
    compra.get("auto_id")  # 🔥 CLAVE
))
        conn.commit()

        # 🔔 aviso al admin
        for admin in ADMINS:
            await context.bot.send_message(
                chat_id=admin,
                text="📥 Nuevo comprobante de AUTO"
            )

        await update.message.reply_text("✅ Comprobante enviado, espera confirmación.")
        context.user_data["esperando_comprobante"] = False
        return


    # ================= COMPROBANTE CUENTAS =================
    if context.user_data.get("esperando_comprobante_cuenta"):
        user = update.effective_user
        compra = context.user_data.get("compra")

        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        cursor.execute("""
        INSERT INTO comprobantes_cuentas 
        (user_id, nombre, precio, foto, fecha)
        VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.first_name,
            compra["precio"],
            foto,
            fecha
        ))
        conn.commit()

        # 🔔 aviso al admin
        for admin in ADMINS:
            await context.bot.send_message(
                chat_id=admin,
                text="📥 Nuevo comprobante de CUENTA"
            )

        await update.message.reply_text("✅ Comprobante enviado")
        context.user_data["esperando_comprobante_cuenta"] = False
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

async def ver_comprobantes(update, context):
    query = update.callback_query
    await query.answer()

    cursor.execute("SELECT * FROM comprobantes")
    data = cursor.fetchall()

    if not data:
        await query.message.edit_text("📭 No hay comprobantes")
        return

    context.user_data["comprobantes"] = data
    context.user_data["index_comp"] = 0

    await mostrar_comprobante(query, context)

async def mostrar_comprobante(query, context):
    data = context.user_data["comprobantes"]
    i = context.user_data["index_comp"]

    comp = data[i]

    texto = f"""
📄 <b>Comprobante #{comp[0]}</b>

👤 {comp[2]}
🆔 {comp[1]}

📦 {comp[3]}
📂 {comp[4]}
💰 {comp[5]}

🕒 {comp[8]}
"""

    keyboard = [
    [
        InlineKeyboardButton("⬅️", callback_data="prev_comp"),
        InlineKeyboardButton("➡️", callback_data="next_comp")
    ],
    [InlineKeyboardButton("🚗 Ver auto", callback_data="ver_auto_comp")],
    [
        InlineKeyboardButton("✅ Pago confirmado", callback_data=f"confirmar_pago_{comp[0]}"),
        InlineKeyboardButton("❌ Pago rechazado", callback_data=f"rechazar_pago_{comp[0]}")
    ],
    [
        InlineKeyboardButton("🚫 Bloquear usuario", callback_data=f"bloquear_{comp[1]}")
    ],
    [InlineKeyboardButton("🔙 Admin", callback_data="admin")]
]

    await query.message.delete()

    await query.message.chat.send_photo(
        photo=comp[6],
        caption=texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def navegar_comp(update, context):
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("comprobantes")

    if not data:
        await update.callback_query.answer("⚠️ No hay comprobantes cargados", show_alert=True)
        return
    i = context.user_data["index_comp"]

    if query.data == "next_comp":
        i = (i + 1) % len(data)
    else:
        i = (i - 1) % len(data)

    context.user_data["index_comp"] = i
    await mostrar_comprobante(query, context)

async def ver_auto_comp(update, context):
    query = update.callback_query
    await query.answer()

    data = context.user_data["comprobantes"]
    i = context.user_data["index_comp"]

    comp = data[i]

    keyboard = [
        [InlineKeyboardButton("🔙 Regresar", callback_data="volver_comp")]
    ]

    await query.message.delete()

    await query.message.chat.send_photo(
        photo=comp[7],
        caption=f"🚗 Producto comprado\n💰 {comp[5]}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def entregar(update, context):
    query = update.callback_query
    await query.answer()

    comp_id = int(query.data.split("_")[1])

    cursor.execute("SELECT user_id FROM comprobantes WHERE id=?", (comp_id,))
    user_id = cursor.fetchone()[0]

    # 📩 mensaje al usuario
    keyboard = [
        [InlineKeyboardButton("💬 Hablar con admin", url=f"tg://user?id={context.bot.id}")]
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text="✅ Tu pago ha sido verificado\n💬 Contacta con el admin",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # 🧹 eliminar comprobante
    cursor.execute("DELETE FROM comprobantes WHERE id=?", (comp_id,))
    conn.commit()

    await query.message.edit_caption("✅ Pedido entregado")
async def confirmar_pago(update, context):
    query = update.callback_query
    await query.answer()

    comp_id = int(query.data.split("_")[2])

    # 🔍 obtener comprobante
    cursor.execute("SELECT * FROM comprobantes WHERE id=?", (comp_id,))
    comp = cursor.fetchone()

    if not comp:
        await query.message.reply_text("❌ Comprobante no encontrado")
        return

    user_id = comp[1]
    nombre = comp[2]
    categoria = comp[4]
    precio = comp[5]
    fecha = comp[8]
    auto_id = comp[9] if len(comp) > 9 else None  # 👈 IMPORTANTE
    if not auto_id:
        await query.message.reply_text("❌ Este comprobante no tiene auto_id (viejo)")
        return
    # 🔍 obtener auto REAL
    cursor.execute("SELECT * FROM autos WHERE id=?", (auto_id,))
    auto = cursor.fetchone()

    if not auto:
        await query.message.reply_text("❌ Auto no encontrado (posible error en DB)")
        return

    media = auto[2]  # file_id (foto o video)
    correo = auto[5] if len(auto) > 5 else "No disponible"

    # =========================
    # 📢 MENSAJE REFERENCIA
    # =========================
    texto_ref = f"""
✅ <b>VENTA CONFIRMADA</b>

👤 Cliente: {nombre}
🆔 ID: {user_id}

🚗 Auto: {categoria}
💰 Precio: {precio}

🕒 {fecha}
"""

    try:
        if str(media).startswith("BA"):  # 🎥 VIDEO
            await context.bot.send_video(
                chat_id=CANAL_REFERENCIAS,
                video=media,
                caption=texto_ref,
                parse_mode="HTML"
            )
        else:  # 📸 FOTO
            await context.bot.send_photo(
                chat_id=CANAL_REFERENCIAS,
                photo=media,
                caption=texto_ref,
                parse_mode="HTML"
            )
    except Exception as e:
        print("Error enviando referencia:", e)

    # =========================
    # 📦 MENSAJE ADMIN
    # =========================
    texto_admin = f"""
📦 <b>Nueva venta confirmada</b>

👤 Usuario: {nombre}
🆔 ID: {user_id}

🚗 Auto comprado
📂 {categoria}
💰 {precio}

📧 Correo:
{correo}

📌 Instrucciones:
1. Abrir correo
2. Buscar auto
3. Verificar datos
4. Entregar
5. Presionar botón
"""

    keyboard = [
        [InlineKeyboardButton("💬 Chatear", url=f"tg://user?id={user_id}")],
        [InlineKeyboardButton("✅ Auto entregado", callback_data=f"entregado_final_{comp_id}")]
    ]

    # enviar con media correcta
    if str(media).startswith("BA"):
        await query.message.reply_video(
            video=media,
            caption=texto_admin,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await query.message.reply_photo(
            photo=media,
            caption=texto_admin,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

async def entregado_final(update, context):
    query = update.callback_query
    await query.answer()

    comp_id = int(query.data.split("_")[2])

    cursor.execute("SELECT user_id FROM comprobantes WHERE id=?", (comp_id,))
    user_id = cursor.fetchone()[0]

    # 📩 usuario
    await context.bot.send_message(
        chat_id=user_id,
        text="🎉 Gracias por tu compra\nTu auto ya fue entregado 🚗"
    )

    # ➕ sumar compra
    cursor.execute("""
    UPDATE usuarios SET compras = compras + 1 WHERE user_id=?
    """, (user_id,))

    # 🧹 borrar comprobante
    cursor.execute("DELETE FROM comprobantes WHERE id=?", (comp_id,))
    conn.commit()

    await query.message.reply_text("✅ Auto marcado como entregado")

async def rechazar_pago(update, context):
    query = update.callback_query
    await query.answer()

    comp_id = int(query.data.split("_")[2])

    # obtener usuario
    cursor.execute("SELECT user_id FROM comprobantes WHERE id=?", (comp_id,))
    result = cursor.fetchone()

    if not result:
        await query.message.reply_text("❌ Comprobante no encontrado")
        return

    user_id = result[0]

    # avisar usuario
    await context.bot.send_message(
        chat_id=user_id,
        text="❌ Tu pago no fue aprobado, intenta nuevamente"
    )

    # 🧹 BORRAR comprobante
    cursor.execute("DELETE FROM comprobantes WHERE id=?", (comp_id,))
    conn.commit()

    await query.message.reply_text("🗑 Comprobante eliminado")

    # 🔄 ACTUALIZAR LISTA EN TIEMPO REAL
    data = context.user_data.get("comprobantes", [])

    data = [c for c in data if c[0] != comp_id]  # quitar el eliminado

    if not data:
        await query.message.reply_text("📭 No hay más comprobantes")
        return

    context.user_data["comprobantes"] = data
    context.user_data["index_comp"] = 0

    await mostrar_comprobante(query, context)

async def confirmar_borrado(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("✅ Sí, borrar todo", callback_data="confirmar_borrado_total")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="admin")]
    ]

    await query.message.edit_text(
        "⚠️ ¿Seguro que quieres borrar TODOS los comprobantes?\n\nEsta acción no se puede deshacer",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def borrar_comprobantes_total(update, context):
    query = update.callback_query
    await query.answer()

    cursor.execute("DELETE FROM comprobantes")
    conn.commit()

    await query.message.edit_text("🗑 Todos los comprobantes fueron eliminados")

async def borrar_auto(update, context):
    query = update.callback_query
    await query.answer()

    auto_id = int(query.data.split("_")[2])

    cursor.execute("DELETE FROM autos WHERE id=?", (auto_id,))
    conn.commit()

    await query.message.edit_caption("🗑 Auto eliminado correctamente")

async def borrar_todos_autos(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("⚠️ Sí, borrar TODO", callback_data="confirmar_borrar_autos")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="admin")]
    ]

    await query.message.edit_text(
        "⚠️ Esto borrará TODOS los autos.\n¿Seguro?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirmar_borrar_autos(update, context):
    query = update.callback_query
    await query.answer()

    cursor.execute("DELETE FROM autos")
    conn.commit()

    await query.message.edit_text("🗑 Todos los autos fueron eliminados")

async def comprar_cuenta(update, context):
    query = update.callback_query

    try:
        await query.answer()
    except:
        pass

    cuentas = context.user_data.get("cuentas")
    i = context.user_data.get("index_cuenta")

    if not cuentas:
        return

    cuenta = cuentas[i]

    context.user_data["compra"] = {
        "tipo": "cuenta",
        "categoria": cuenta[1],
        "foto": cuenta[2],  # es video pero lo usamos igual
        "precio": cuenta[3]
    }

    texto = f"""
👤 Estás comprando una cuenta:

📂 Tipo: {cuenta[1]}
💰 Precio: {cuenta[3]}


💸 MÉTODOS DE PAGO DISPONIBLES 💸  

━━━━━━━━━━━━━━━  
💳 Transferencia (Spin by Oxxo)  
👤 Nombre: Reyna Margarita Hernández  
🔢 7289 6900 0155 6615 39  

🏪 Depósito en Oxxo  
🔢 2242 1702 9026 6032  

━━━━━━━━━━━━━━━  

🌎 INTERNACIONAL  

💰 PayPal  
📩 albertoya@hotmail.com  

━━━━━━━━━━━━━━━  

⚡ Envía tu comprobante para confirmar tu pago
💸 Total a pagar: {cuenta[3]}
"""

    keyboard = [
        [InlineKeyboardButton("💰 Pagar", callback_data="pagar")],
        [InlineKeyboardButton("⬅️ Atrás", callback_data="back")]
    ]

    await query.message.reply_video(
        video=cuenta[2],
        caption=texto,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirmar_cuenta(update, context):
    query = update.callback_query
    await query.answer()

    # 🔢 GENERAR NÚMERO DE CUENTA
    cursor.execute("SELECT COUNT(*) FROM cuentas")
    numero = cursor.fetchone()[0] + 1

    cursor.execute("""
    INSERT INTO cuentas (categoria, video, precio, correo, numero)
    VALUES (?, ?, ?, ?, ?)
    """, (
        context.user_data["categoria"],
        context.user_data["video"],
        context.user_data["precio"],
        context.user_data["correo"],
        numero
    ))

    conn.commit()

    await query.message.edit_caption(f"✅ Cuenta #{numero} agregada")
    context.user_data.clear()
async def ver_comprobantes_cuentas(update, context):
    query = update.callback_query
    await query.answer()

    cursor.execute("SELECT * FROM comprobantes_cuentas")
    data = cursor.fetchall()

    if not data:
        await query.message.edit_text("📭 No hay comprobantes de cuentas")
        return

    context.user_data["comp_cuentas"] = data
    context.user_data["index_cc"] = 0

    await mostrar_comp_cuenta(query, context)
async def navegar_comp_cuenta(update, context):
    query = update.callback_query
    await query.answer()

    data = context.user_data["comp_cuentas"]
    i = context.user_data["index_cc"]

    if query.data == "next_cc":
        i = (i + 1) % len(data)
    else:
        i = (i - 1) % len(data)

    context.user_data["index_cc"] = i

    await mostrar_comp_cuenta(query, context)


async def mostrar_comp_cuenta(query, context):
    data = context.user_data["comp_cuentas"]
    i = context.user_data["index_cc"]
    comp = data[i]

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_cc"),
            InlineKeyboardButton("➡️", callback_data="next_cc")
        ],
        [
            InlineKeyboardButton("✅ Aceptar", callback_data=f"aceptar_cc_{comp[0]}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_cc_{comp[0]}")
        ],
        [
            InlineKeyboardButton("🚫 Bloquear", callback_data=f"bloquear_{comp[1]}")
        ]
    ]

    try:
        await query.message.delete()
    except:
        pass

    try:
        await query.message.chat.send_photo(
            photo=comp[4],
            caption=f"💰 Precio: {comp[3]}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print("ERROR:", e)
        await query.message.chat.send_message("❌ Error mostrando comprobante")
async def aceptar_cc(update, context):
    query = update.callback_query
    await query.answer()

    comp_id = int(query.data.split("_")[2])

    cursor.execute("SELECT * FROM comprobantes_cuentas WHERE id=?", (comp_id,))
    comp = cursor.fetchone()

    user_id = comp[1]

    # 🔍 buscar cuenta
    cursor.execute("SELECT * FROM cuentas WHERE precio=?", (comp[3],))
    cuenta = cursor.fetchone()

    correo = cuenta[4]

    keyboard = [
        [InlineKeyboardButton("💬 Chat", url=f"tg://user?id={user_id}")],
        [InlineKeyboardButton("✅ Entregada", callback_data=f"entregada_cuenta_{comp_id}")]
    ]

    await query.message.reply_text(f"""
✅ Comprobante aceptado

📧 Clona este correo:
{correo}

💬 Contacta al usuario para entrega
""", reply_markup=InlineKeyboardMarkup(keyboard))

async def entregada_cuenta(update, context):
    query = update.callback_query
    await query.answer()

    comp_id = int(query.data.split("_")[2])

    cursor.execute("SELECT user_id FROM comprobantes_cuentas WHERE id=?", (comp_id,))
    user_id = cursor.fetchone()[0]

    await context.bot.send_message(
        chat_id=user_id,
        text="🎉 Gracias por tu compra 👤"
    )

    cursor.execute("DELETE FROM comprobantes_cuentas WHERE id=?", (comp_id,))
    conn.commit()

    await query.message.reply_text("✅ Cuenta entregada")

async def pagar(update, context):
    query = update.callback_query
    await query.answer()

    compra = context.user_data.get("compra", {})

    if compra.get("tipo") == "cuenta":
        context.user_data["esperando_comprobante_cuenta"] = True
    else:
        context.user_data["esperando_comprobante"] = True

    await query.message.reply_text("📸 Envía tu comprobante de pago aquí.")

async def pedir_reseña(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data["modo_reseña"] = True

    await query.message.reply_text(
        "⭐ Escribe tu reseña sobre el servicio\n\n(Ejemplo: Buen servicio, rápido 🔥)"
    )

# ⭐ RESEÑAS
async def ver_reseñas(update, context):
    query = update.callback_query
    await query.answer()

    cursor.execute("SELECT * FROM reseñas ORDER BY id DESC")
    data = cursor.fetchall()

    if not data:
        await query.message.edit_text("📭 No hay reseñas")
        return

    context.user_data["reseñas"] = data
    context.user_data["index_reseña"] = 0

    await mostrar_reseña(query, context)

async def mostrar_reseña(query, context):
    data = context.user_data["reseñas"]
    i = context.user_data["index_reseña"]

    r = data[i]

    texto = f"""
⭐ <b>Reseña #{r[0]}</b>

👤 {r[2]}
🆔 {r[1]}

💬 {r[3]}

🕒 {r[4]}
"""

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_reseña"),
            InlineKeyboardButton("➡️", callback_data="next_reseña")
        ],
        [InlineKeyboardButton("🔙 Admin", callback_data="admin")]
    ]

    await query.message.delete()

    await query.message.chat.send_message(
        text=texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def navegar_reseñas(update, context):
    query = update.callback_query
    await query.answer()

    data = context.user_data["reseñas"]
    i = context.user_data["index_reseña"]

    if query.data == "next_reseña":
        i = (i + 1) % len(data)
    else:
        i = (i - 1) % len(data)

    context.user_data["index_reseña"] = i

    await mostrar_reseña(query, context)

async def ver_stats(update, context):
    query = update.callback_query
    await query.answer()

    # 👥 usuarios totales
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]

    # 🛒 compras totales
    cursor.execute("SELECT SUM(compras) FROM usuarios")
    compras = cursor.fetchone()[0] or 0

    # ⭐ reseñas
    cursor.execute("SELECT COUNT(*) FROM reseñas")
    reseñas = cursor.fetchone()[0]

    # 🚫 bloqueados
    cursor.execute("SELECT COUNT(*) FROM bloqueados")
    bloqueados = cursor.fetchone()[0]

    # 💰 ingresos (de comprobantes)
    cursor.execute("SELECT precio FROM comprobantes")
    precios = cursor.fetchall()

    total_dinero = 0
    for p in precios:
        try:
            total_dinero += float(str(p[0]).replace("$", "").replace("MXN", "").strip())
        except:
            pass

    texto = f"""
📊 <b>ESTADÍSTICAS DEL BOT</b>

👥 Usuarios: {usuarios}
🛒 Compras: {compras}
💰 Ingresos: ${total_dinero}

⭐ Reseñas: {reseñas}
🚫 Bloqueados: {bloqueados}
"""

    keyboard = [
        [InlineKeyboardButton("🔙 Admin", callback_data="admin")]
    ]

    await query.message.edit_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def mis_compras(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    cursor.execute("""
    SELECT * FROM comprobantes 
    WHERE user_id=? 
    ORDER BY id DESC
    """, (user_id,))

    data = cursor.fetchall()

    if not data:
        await query.message.edit_text("📭 No tienes compras aún")
        return

    context.user_data["mis_compras"] = data
    context.user_data["index_mc"] = 0

    await mostrar_mi_compra(query, context)

async def mis_compras(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    cursor.execute("""
    SELECT * FROM comprobantes 
    WHERE user_id=? 
    ORDER BY id DESC
    """, (user_id,))

    data = cursor.fetchall()

    if not data:
        try:
            await query.message.edit_text("📭 No tienes compras aún")
        except:
            await query.message.delete()
            await query.message.chat.send_message("📭 No tienes compras aún")
        return

    context.user_data["mis_compras"] = data
    context.user_data["index_mc"] = 0

    await mostrar_mi_compra(query, context)
async def mostrar_mi_compra(query, context):
    data = context.user_data["mis_compras"]
    i = context.user_data["index_mc"]

    comp = data[i]

    texto = f"""
📦 <b>Compra #{comp[0]}</b>

🚗 {comp[3]}
📂 {comp[4]}
💰 {comp[5]}

🕒 {comp[8]}
"""

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_mc"),
            InlineKeyboardButton("➡️", callback_data="next_mc")
        ],
        [InlineKeyboardButton("🏠 Menú", callback_data="menu")]
    ]

    try:
        await query.message.delete()
    except:
        pass

    await query.message.chat.send_photo(
        photo=comp[7],
        caption=texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def navegar_mis_compras(update, context):
    query = update.callback_query
    await query.answer()

    data = context.user_data["mis_compras"]
    i = context.user_data["index_mc"]

    if query.data == "next_mc":
        i = (i + 1) % len(data)
    else:
        i = (i - 1) % len(data)

    context.user_data["index_mc"] = i

    await mostrar_mi_compra(query, context)

async def borrar_anterior(update):
    query = update.callback_query
    try:
        await query.message.delete()
    except:
        pass

async def resetear(update, context):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMINS:
        return

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    cursor.execute("""
    INSERT OR REPLACE INTO config (clave, valor)
    VALUES ('ultimo_reset', ?)
    """, (fecha,))
    conn.commit()

    await query.message.edit_text("✅ Conteo reiniciado correctamente")
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

app.add_handler(CallbackQueryHandler(detalle_auto, pattern="^detalle_auto$"))
app.add_handler(CallbackQueryHandler(detalle_uno, pattern="^detalle_uno$"))

app.add_handler(CallbackQueryHandler(navegar_detalle, pattern="^(prev_detalle|next_detalle)$"))

app.add_handler(CallbackQueryHandler(extra_si, pattern="^add_extra_si$"))
app.add_handler(CallbackQueryHandler(extra_no, pattern="^add_extra_no$"))
app.add_handler(CallbackQueryHandler(ver_comprobantes, pattern="^ver_comprobantes$"))
app.add_handler(CallbackQueryHandler(navegar_comp, pattern="^(prev_comp|next_comp)$"))
app.add_handler(CallbackQueryHandler(ver_auto_comp, pattern="^ver_auto_comp$"))
app.add_handler(CallbackQueryHandler(entregar, pattern="^entregar_"))

app.add_handler(CallbackQueryHandler(confirmar_auto, pattern="^confirmar_auto$"))
app.add_handler(CallbackQueryHandler(confirmar_cuenta, pattern="^confirmar_cuenta$"))
app.add_handler(CallbackQueryHandler(bloquear_usuario, pattern="^bloquear_"))
app.add_handler(CallbackQueryHandler(cancelar, pattern="^cancelar$"))
app.add_handler(CallbackQueryHandler(ver_bloqueados, pattern="^ver_bloqueados$"))
app.add_handler(CallbackQueryHandler(desbloquear_usuario, pattern="^desbloquear_"))
app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(repetir_uno, pattern="^repetir_uno$"))
app.add_handler(CallbackQueryHandler(repetir_autos, pattern="^repetir_autos$"))
app.add_handler(CallbackQueryHandler(confirmar_pago, pattern="^confirmar_pago_"))
app.add_handler(CallbackQueryHandler(entregado_final, pattern="^entregado_final_"))
app.add_handler(CallbackQueryHandler(rechazar_pago, pattern="^rechazar_pago_"))
app.add_handler(CallbackQueryHandler(confirmar_borrado, pattern="^borrar_comprobantes$"))
app.add_handler(CallbackQueryHandler(borrar_comprobantes_total, pattern="^confirmar_borrado_total$"))
app.add_handler(CallbackQueryHandler(borrar_auto, pattern="^borrar_auto_"))
app.add_handler(CallbackQueryHandler(borrar_todos_autos, pattern="^borrar_todos_autos$"))
app.add_handler(CallbackQueryHandler(confirmar_borrar_autos, pattern="^confirmar_borrar_autos$"))
app.add_handler(CallbackQueryHandler(comprar_cuenta, pattern="^comprar_cuenta$"))
app.add_handler(CallbackQueryHandler(ver_comprobantes_cuentas, pattern="^ver_comprobantes_cuentas$"))
app.add_handler(CallbackQueryHandler(entregada_cuenta, pattern="^entregada_cuenta_"))


app.add_handler(CallbackQueryHandler(navegar_comp_cuenta, pattern="^(prev_cc|next_cc)$"))

app.add_handler(CallbackQueryHandler(aceptar_cc, pattern="^aceptar_cc_"))
app.add_handler(CallbackQueryHandler(aceptar_pago, pattern="^aceptar_[0-9]+$"))
app.add_handler(CallbackQueryHandler(pedir_reseña, pattern="^reseña$"))
app.add_handler(CallbackQueryHandler(ver_reseñas, pattern="^ver_reseñas$"))
app.add_handler(CallbackQueryHandler(navegar_reseñas, pattern="^(prev_reseña|next_reseña)$"))
app.add_handler(CallbackQueryHandler(ver_stats, pattern="^stats$"))
app.add_handler(CallbackQueryHandler(mis_compras, pattern="^mis_compras$"))
app.add_handler(CallbackQueryHandler(navegar_mis_compras, pattern="^(prev_mc|next_mc)$"))
app.add_handler(CallbackQueryHandler(imforma_cion, pattern="^imforma_cion$"))
app.add_handler(CallbackQueryHandler(resetear, pattern="resetear"))
app.add_handler(CallbackQueryHandler(ver_deportivos, pattern="^deportivos$"))
app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))

app.add_handler(MessageHandler(filters.PHOTO, recibir_foto))
app.add_handler(MessageHandler(filters.VIDEO, recibir_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_precio_general))

app.run_polling()