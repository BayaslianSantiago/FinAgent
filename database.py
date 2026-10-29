import os
import sqlite3
import hashlib
import datetime
import json
from typing import Optional, Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(__file__), "finanzas.db")

def get_connection() -> sqlite3.Connection:
    """Retorna una conexión a la base de datos SQLite con soporte para diccionarios (Row)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==============================================================================
# SEGURIDAD Y HASHING DE CONTRASEÑAS (Ley 26.343 / Ciberseguridad)
# ==============================================================================

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Genera un hash seguro usando PBKDF2 y SHA-256 con salt aleatorio."""
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash almacenado."""
    calculated_hash, _ = hash_password(password, salt)
    return calculated_hash == stored_hash

# ==============================================================================
# INICIALIZACIÓN DEL ESQUEMA RELACIONAL (DDL)
# ==============================================================================

def init_db():
    """Crea las tablas de la base de datos si no existen e inserta usuario demo inicial."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Tabla de Usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            perfil_inversor TEXT DEFAULT 'Moderado' CHECK(perfil_inversor IN ('Conservador', 'Moderado', 'Arriesgado')),
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Tabla de Presupuestos Mensuales (Regla 50/30/20)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS presupuestos_mensuales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            mes_año TEXT NOT NULL, -- Formato 'YYYY-MM'
            ingreso_estimado REAL NOT NULL,
            limite_necesidades_50 REAL,
            limite_gustos_30 REAL,
            meta_ahorro_20 REAL,
            notas TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
            UNIQUE(usuario_id, mes_año)
        );
        """)

        # 3. Tabla de Movimientos (Ingresos y Gastos)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('ingreso', 'gasto')),
            categoria TEXT NOT NULL,
            clasificacion_regla TEXT CHECK(clasificacion_regla IN ('necesidad', 'gusto', 'ahorro')),
            monto REAL NOT NULL,
            descripcion TEXT,
            fecha DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        );
        """)

        # 4. Tabla de Metas de Ahorro
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas_ahorro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nombre_meta TEXT NOT NULL,
            monto_objetivo REAL NOT NULL,
            monto_acumulado REAL DEFAULT 0.0,
            fecha_limite DATE,
            estado TEXT DEFAULT 'en_progreso' CHECK(estado IN ('en_progreso', 'alcanzada', 'pausada')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        );
        """)

        # 5. Tabla de Contexto Cualitativo para la IA
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contexto_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            clave TEXT NOT NULL,
            valor TEXT NOT NULL,
            actualizado_el TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
            UNIQUE(usuario_id, clave)
        );
        """)

        conn.commit()

        # Crear usuario demo inicial si la base está vacía
        cursor.execute("SELECT COUNT(*) as count FROM usuarios")
        if cursor.fetchone()["count"] == 0:
            demo_hash, demo_salt = hash_password("demo123")
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, salt, nombre_completo, perfil_inversor)
                VALUES (?, ?, ?, ?, ?)
            """, ("demo", demo_hash, demo_salt, "Martín Gómez", "Moderado"))
            
            user_id = cursor.lastrowid
            current_month = datetime.date.today().strftime("%Y-%m")
            
            # Presupuesto demo inicial ($800.000 de sueldo estimado)
            ingreso = 800000.0
            cursor.execute("""
                INSERT INTO presupuestos_mensuales 
                (usuario_id, mes_año, ingreso_estimado, limite_necesidades_50, limite_gustos_30, meta_ahorro_20, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, current_month, ingreso, ingreso * 0.50, ingreso * 0.30, ingreso * 0.20, "Presupuesto inicial demo"))
            
            # Movimientos de ejemplo
            sample_txs = [
                (user_id, "ingreso", "Sueldo", "ahorro", 800000.0, "Cobro de sueldo mensual"),
                (user_id, "gasto", "Alquiler", "necesidad", 280000.0, "Alquiler departamento"),
                (user_id, "gasto", "Servicios", "necesidad", 45000.0, "Luz, Gas e Internet"),
                (user_id, "gasto", "Supermercado", "necesidad", 95000.0, "Compras de alimentos y limpieza"),
                (user_id, "gasto", "Salidas / Ocio", "gusto", 42000.0, "Cena fin de semana"),
                (user_id, "gasto", "Streaming", "gusto", 12000.0, "Netflix y Spotify")
            ]
            cursor.executemany("""
                INSERT INTO movimientos (usuario_id, tipo, categoria, clasificacion_regla, monto, descripcion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, sample_txs)
            
            # Meta de ahorro de ejemplo: Fondo de Emergencia
            cursor.execute("""
                INSERT INTO metas_ahorro (usuario_id, nombre_meta, monto_objetivo, monto_acumulado, fecha_limite)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, "Fondo de Emergencia", 1200000.0, 350000.0, "2026-12-31"))

            # Contexto IA inicial
            cursor.execute("""
                INSERT INTO contexto_ia (usuario_id, clave, valor)
                VALUES (?, ?, ?)
            """, (user_id, "ocupacion", "Empleado en relación de dependencia con monotributo complementario"))
            
            conn.commit()
            print("[Database] Base de datos 'finanzas.db' inicializada con usuario 'demo' y datos de prueba.")

# ==============================================================================
# FUNCIONES DE USUARIOS Y AUTENTICACIÓN
# ==============================================================================

def register_user(username: str, password: str, nombre_completo: str, perfil_inversor: str = "Moderado") -> Optional[Dict[str, Any]]:
    """Registra un nuevo usuario con credenciales encriptadas."""
    pwd_hash, salt = hash_password(password)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, salt, nombre_completo, perfil_inversor)
                VALUES (?, ?, ?, ?, ?)
            """, (username.strip().lower(), pwd_hash, salt, nombre_completo.strip(), perfil_inversor))
            conn.commit()
            user_id = cursor.lastrowid
            return {"id": user_id, "username": username, "nombre_completo": nombre_completo, "perfil_inversor": perfil_inversor}
    except sqlite3.IntegrityError:
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Autentica a un usuario verificando el hash de la contraseña."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username.strip().lower(),))
        row = cursor.fetchone()
        if not row:
            return None
        if verify_password(password, row["password_hash"], row["salt"]):
            return {
                "id": row["id"],
                "username": row["username"],
                "nombre_completo": row["nombre_completo"],
                "perfil_inversor": row["perfil_inversor"]
            }
    return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, nombre_completo, perfil_inversor, fecha_registro FROM usuarios WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ==============================================================================
# OPERACIONES FINANCIERAS (MOVIMIENTOS, BALANCES, METAS)
# ==============================================================================

def sync_dashboard_json(usuario_id: int = 1):
    """Sincroniza automáticamente los datos de la base de datos con el archivo estático del dashboard."""
    try:
        data = {
            "summary": get_monthly_summary(usuario_id),
            "transactions": get_recent_transactions(usuario_id, limit=50),
            "goals": get_goals(usuario_id),
            "user": get_user_by_id(usuario_id) or {"nombre_completo": "Martín Gómez", "perfil_inversor": "Moderado"}
        }
        os.makedirs("public", exist_ok=True)
        with open("public/data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Database] Error al sincronizar dashboard JSON: {e}")

def add_transaction(usuario_id: int, tipo: str, categoria: str, monto: float, descripcion: str = "", clasificacion_regla: Optional[str] = None, fecha: Optional[str] = None) -> int:
    """Registra un ingreso o gasto."""
    # Autoclasificación por defecto si no viene especificada
    if not clasificacion_regla:
        cat_lower = categoria.lower()
        if tipo == "ingreso":
            clasificacion_regla = "ahorro"
        elif any(c in cat_lower for c in ["alquiler", "luz", "gas", "agua", "internet", "comida", "super", "farmacia", "salud", "transporte"]):
            clasificacion_regla = "necesidad"
        else:
            clasificacion_regla = "gusto"

    if not fecha:
        fecha = datetime.date.today().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO movimientos (usuario_id, tipo, categoria, clasificacion_regla, monto, descripcion, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario_id, tipo.lower(), categoria.strip(), clasificacion_regla, float(monto), descripcion.strip(), fecha))
        conn.commit()
        last_id = cursor.lastrowid
    
    sync_dashboard_json(usuario_id)
    return last_id


def get_monthly_summary(usuario_id: int, mes_año: Optional[str] = None) -> Dict[str, Any]:
    """Calcula el balance del mes con desglose 50/30/20 y saldo disponible."""
    if not mes_año:
        mes_año = datetime.date.today().strftime("%Y-%m")

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Consultar movimientos del mes
        cursor.execute("""
            SELECT tipo, clasificacion_regla, SUM(monto) as total
            FROM movimientos
            WHERE usuario_id = ? AND strftime('%Y-%m', fecha) = ?
            GROUP BY tipo, clasificacion_regla
        """, (usuario_id, mes_año))
        rows = cursor.fetchall()

        total_ingresos = 0.0
        total_gastos = 0.0
        necesidades = 0.0
        gustos = 0.0
        ahorro_registrado = 0.0

        for r in rows:
            monto = float(r["total"] or 0.0)
            if r["tipo"] == "ingreso":
                total_ingresos += monto
            else:
                total_gastos += monto
                if r["clasificacion_regla"] == "necesidad":
                    necesidades += monto
                elif r["clasificacion_regla"] == "gusto":
                    gustos += monto
                else:
                    ahorro_registrado += monto

        saldo_disponible = total_ingresos - total_gastos

        # Consultar presupuesto planificado si existe
        cursor.execute("""
            SELECT * FROM presupuestos_mensuales
            WHERE usuario_id = ? AND mes_año = ?
        """, (usuario_id, mes_año))
        presupuesto = cursor.fetchone()

        return {
            "mes_año": mes_año,
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "saldo_disponible": saldo_disponible,
            "desglose_gastos": {
                "necesidades_50": necesidades,
                "gustos_30": gustos,
                "ahorro_inversion": ahorro_registrado
            },
            "porcentajes_actuales": {
                "necesidades_pct": round((necesidades / total_ingresos * 100), 1) if total_ingresos > 0 else 0,
                "gustos_pct": round((gustos / total_ingresos * 100), 1) if total_ingresos > 0 else 0,
                "ahorro_pct": round(((saldo_disponible + ahorro_registrado) / total_ingresos * 100), 1) if total_ingresos > 0 else 0
            },
            "presupuesto_planificado": dict(presupuesto) if presupuesto else None
        }

def get_recent_transactions(usuario_id: int, limit: int = 8) -> List[Dict[str, Any]]:
    """Retorna los últimos movimientos registrados."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tipo, categoria, clasificacion_regla, monto, descripcion, fecha
            FROM movimientos
            WHERE usuario_id = ?
            ORDER BY fecha DESC, id DESC
            LIMIT ?
        """, (usuario_id, limit))
        return [dict(r) for r in cursor.fetchall()]

def get_goals(usuario_id: int) -> List[Dict[str, Any]]:
    """Retorna las metas de ahorro activas del usuario."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre_meta, monto_objetivo, monto_acumulado, fecha_limite, estado
            FROM metas_ahorro
            WHERE usuario_id = ?
            ORDER BY id ASC
        """, (usuario_id,))
        return [dict(r) for r in cursor.fetchall()]

def add_or_update_goal(usuario_id: int, nombre_meta: str, monto_objetivo: float, fecha_limite: Optional[str] = None) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metas_ahorro (usuario_id, nombre_meta, monto_objetivo, fecha_limite)
            VALUES (?, ?, ?, ?)
        """, (usuario_id, nombre_meta.strip(), float(monto_objetivo), fecha_limite))
        conn.commit()
        return cursor.lastrowid

def deposit_to_goal(usuario_id: int, nombre_meta: str, monto: float) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE metas_ahorro
            SET monto_acumulado = monto_acumulado + ?
            WHERE usuario_id = ? AND LOWER(nombre_meta) LIKE ?
        """, (float(monto), usuario_id, f"%{nombre_meta.strip().lower()}%"))
        conn.commit()
        return cursor.rowcount > 0

def delete_transaction(usuario_id: int, transaction_id: int) -> bool:
    """Elimina un movimiento registrado previamente perteneciente al usuario."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movimientos WHERE id = ? AND usuario_id = ?", (transaction_id, usuario_id))
        conn.commit()
        ok = cursor.rowcount > 0
    if ok:
        sync_dashboard_json(usuario_id)
    return ok

def update_transaction(usuario_id: int, transaction_id: int, monto: Optional[float] = None, tipo: Optional[str] = None, categoria: Optional[str] = None, descripcion: Optional[str] = None) -> bool:
    """Modifica los campos de un movimiento existente."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Verificar existencia
        cursor.execute("SELECT * FROM movimientos WHERE id = ? AND usuario_id = ?", (transaction_id, usuario_id))
        row = cursor.fetchone()
        if not row:
            return False

        new_monto = float(monto) if monto is not None else row["monto"]
        new_tipo = tipo.lower().strip() if tipo else row["tipo"]
        new_cat = categoria.strip() if categoria else row["categoria"]
        new_desc = descripcion.strip() if descripcion else row["descripcion"]

        # Clasificación automática según el tipo y categoría
        clasificacion = row["clasificacion_regla"]
        if new_tipo == "ingreso":
            clasificacion = "ahorro"
        elif any(c in new_cat.lower() for c in ["alquiler", "luz", "gas", "agua", "internet", "comida", "super", "farmacia", "salud", "transporte"]):
            clasificacion = "necesidad"
        else:
            clasificacion = "gusto"

        cursor.execute("""
            UPDATE movimientos
            SET monto = ?, tipo = ?, categoria = ?, descripcion = ?, clasificacion_regla = ?
            WHERE id = ? AND usuario_id = ?
        """, (new_monto, new_tipo, new_cat, new_desc, clasificacion, transaction_id, usuario_id))
        conn.commit()
        ok = cursor.rowcount > 0
    if ok:
        sync_dashboard_json(usuario_id)
    return ok

def set_monthly_income(usuario_id: int, nuevo_ingreso_total: float, mes_año: Optional[str] = None, descripcion: str = "Ingreso mensual consolidado") -> Dict[str, Any]:
    """
    Fija el ingreso total exacto del usuario para un mes dado.
    Actualiza la tabla de presupuestos 50/30/20 y consolida las transacciones de ingreso
    para que el total de ingresos coincida exactamente con lo que el usuario declara.
    """
    if not mes_año:
        mes_año = datetime.date.today().strftime("%Y-%m")

    nuevo_ingreso_total = max(0.0, float(nuevo_ingreso_total))

    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Actualizar o insertar presupuesto mensual
        cursor.execute("""
            INSERT INTO presupuestos_mensuales (usuario_id, mes_año, ingreso_estimado, limite_necesidades_50, limite_gustos_30, meta_ahorro_20, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(usuario_id, mes_año) DO UPDATE SET
                ingreso_estimado = excluded.ingreso_estimado,
                limite_necesidades_50 = excluded.limite_necesidades_50,
                limite_gustos_30 = excluded.limite_gustos_30,
                meta_ahorro_20 = excluded.meta_ahorro_20,
                notas = excluded.notas
        """, (
            usuario_id,
            mes_año,
            nuevo_ingreso_total,
            nuevo_ingreso_total * 0.50,
            nuevo_ingreso_total * 0.30,
            nuevo_ingreso_total * 0.20,
            f"Fijado por el usuario: ${nuevo_ingreso_total:,.2f}"
        ))

        # 2. Reemplazar los ingresos del mes por el nuevo valor consolidado
        cursor.execute("DELETE FROM movimientos WHERE usuario_id = ? AND strftime('%Y-%m', fecha) = ? AND tipo = 'ingreso'", (usuario_id, mes_año))
        
        if nuevo_ingreso_total > 0:
            cursor.execute("""
                INSERT INTO movimientos (usuario_id, tipo, categoria, clasificacion_regla, monto, descripcion, fecha)
                VALUES (?, 'ingreso', 'Sueldo', 'ahorro', ?, ?, ?)
            """, (usuario_id, nuevo_ingreso_total, descripcion, f"{mes_año}-01"))

        conn.commit()

    sync_dashboard_json(usuario_id)
    return get_monthly_summary(usuario_id, mes_año)

def adjust_monthly_income(usuario_id: int, delta_monto: float, mes_año: Optional[str] = None, descripcion: str = "Ajuste de ingreso") -> Dict[str, Any]:
    """
    Suma o resta dinero al total de ingresos del mes sin tocar los gastos.
    Ej: delta_monto = -1000000 baja los ingresos en 1.000.000.
    """
    if not mes_año:
        mes_año = datetime.date.today().strftime("%Y-%m")

    current = get_monthly_summary(usuario_id, mes_año)
    nuevo_total = max(0.0, current["total_ingresos"] + float(delta_monto))
    return set_monthly_income(usuario_id, nuevo_total, mes_año, descripcion)

def set_user_context(usuario_id: int, clave: str, valor: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contexto_ia (usuario_id, clave, valor, actualizado_el)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(usuario_id, clave) DO UPDATE SET valor = excluded.valor, actualizado_el = CURRENT_TIMESTAMP
        """, (usuario_id, clave.strip().lower(), valor.strip()))
        conn.commit()

def get_user_context(usuario_id: int) -> Dict[str, str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT clave, valor FROM contexto_ia WHERE usuario_id = ?", (usuario_id,))
        return {r["clave"]: r["valor"] for r in cursor.fetchall()}

