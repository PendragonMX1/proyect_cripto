import hashlib, json, shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARCHIVO = BASE / "blockchain.json"
RESPALDO = BASE / "blockchain_respaldo.json"
CAMPOS = ("id", "timestamp", "datos", "prev_hash", "hash_actual")
def calcular_hash(id_registro, timestamp, datos, prev_hash):
    contenido = {"id": id_registro, "timestamp": timestamp, "datos": datos, "prev_hash": prev_hash}
    texto = json.dumps(contenido, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()
def crear_registro(id_registro, datos, prev_hash):
    fecha = datetime.now().astimezone().isoformat(timespec="seconds")
    hash_actual = calcular_hash(id_registro, fecha, datos, prev_hash)
    return {"id": id_registro, "timestamp": fecha, "datos": datos, "prev_hash": prev_hash, "hash_actual": hash_actual}
def agregar_a_cadena(cadena, datos):
    anterior = cadena[-1]["hash_actual"] if cadena else "0" * 64
    registro = crear_registro(len(cadena) + 1, datos, anterior)
    cadena.append(registro)
    return registro
def estructura_valida(cadena):
    if not isinstance(cadena, list): return False
    for registro in cadena:
        if not isinstance(registro, dict) or not all(c in registro for c in CAMPOS): return False
        if type(registro["id"]) is not int: return False
        if any(not isinstance(registro[c], str) for c in CAMPOS[1:]): return False
    return True
def guardar_cadena(cadena):
    temporal = ARCHIVO.with_suffix(".tmp")
    try:
        temporal.write_text(json.dumps(cadena, ensure_ascii=False, indent=4), encoding="utf-8")
        temporal.replace(ARCHIVO)
        return True
    except OSError as error:
        print("ERROR al guardar:", error)
        return False

def cargar_cadena():
    if not ARCHIVO.exists():
        print("No existe una base anterior. Se iniciara una cadena vacia.")
        return []
    try:
        cadena = json.loads(ARCHIVO.read_text(encoding="utf-8"))
        if not estructura_valida(cadena):
            raise ValueError("El archivo no tiene los campos o tipos requeridos.")
        print("Base cargada. Registros recuperados:", len(cadena))
        return cadena
    except (OSError, ValueError, UnicodeError) as error:
        print("ERROR al cargar:", error, "\nNo se modificara el archivo.")
        return None

def verificar_integridad(cadena, mostrar=True):
    if not cadena:
        if mostrar: print("No hay registros para verificar.")
        return False
    valida = True
    if mostrar: print("\n=== VERIFICACION DE INTEGRIDAD ===")
    for i, registro in enumerate(cadena):
        errores = []
        recalculado = calcular_hash(registro["id"], registro["timestamp"], registro["datos"], registro["prev_hash"])
        anterior = cadena[i - 1]["hash_actual"] if i else "0" * 64
        if registro["id"] != i + 1:
            errores.append("ID fuera de orden")
        if registro["hash_actual"] != recalculado:
            errores.append("Hash almacenado diferente del recalculado")
        if registro["prev_hash"] != anterior:
            errores.append("prev_hash no coincide con el registro anterior")
        if errores:
            valida = False
            if mostrar:
                print(f"[ERROR] Registro en posicion {i + 1}:", "; ".join(errores))
                print("  Hash almacenado:", registro["hash_actual"])
                print("  Hash recalculado:", recalculado)
        elif mostrar:
            print(f"[OK] Registro {registro['id']} integro y enlazado")
    if mostrar: print("RESULTADO: CADENA VALIDA" if valida else "RESULTADO: CADENA CORRUPTA")
    return valida

def agregar_interactivo(cadena):
    if cadena and not verificar_integridad(cadena, False):
        print("La cadena esta corrupta. Verifica (3) o restaura (8).")
        return
    datos = input("Datos del nuevo registro: ").strip()
    if not datos:
        print("ERROR: No puedes agregar un registro vacio.")
        return
    registro = agregar_a_cadena(cadena, datos)
    if not guardar_cadena(cadena):
        cadena.pop()
        return
    print(f"Registro {registro['id']} guardado correctamente.")
    print("Hash anterior:", registro["prev_hash"])
    print("Hash actual:  ", registro["hash_actual"])

def mostrar_registros(cadena):
    if not cadena:
        print("No hay registros.")
        return
    print("\n=== REGISTROS === Total:", len(cadena))
    for registro in cadena:
        print(f"\n--- REGISTRO {registro['id']} ---")
        for campo in CAMPOS[1:]:
            print(f"{campo}: {registro[campo]}")

def simular_alteracion(cadena):
    if not cadena or not verificar_integridad(cadena, False):
        print("Necesitas una cadena valida y con registros.")
        return
    for registro in cadena:
        print(f"{registro['id']}: {registro['datos']}")
    try:
        numero = int(input("ID a alterar: ").strip())
    except ValueError:
        print("Debes escribir un numero.")
        return
    if not 1 <= numero <= len(cadena):
        print("ID inexistente.")
        return
    nuevo = input("Datos falsificados: ").strip()
    registro = cadena[numero - 1]
    if not nuevo or nuevo == registro["datos"]:
        print("No hubo cambios validos.")
        return
    try:
        shutil.copy2(ARCHIVO, RESPALDO)
    except OSError as error:
        print("No se pudo crear respaldo:", error)
        return
    original = registro["datos"]
    registro["datos"] = nuevo  # Simula el ataque SIN recalcular el hash.
    if not guardar_cadena(cadena):
        registro["datos"] = original
        return
    print(f"Registro {numero} alterado. Respaldo creado.")
    print("Usa la opcion 3 para detectar la alteracion.")

def restaurar_cadena(cadena):
    if not RESPALDO.exists():
        print("No hay respaldo disponible.")
        return
    try:
        recuperada = json.loads(RESPALDO.read_text(encoding="utf-8"))
        if not estructura_valida(recuperada) or not verificar_integridad(recuperada, False):
            print("El respaldo tiene errores y no se restaurara.")
            return
    except (OSError, ValueError, UnicodeError) as error:
        print("ERROR al leer respaldo:", error)
        return
    if guardar_cadena(recuperada):
        cadena[:] = recuperada
        print("Cadena restaurada. Registros:", len(cadena))
def demostrar_hash():
    fecha, anterior = "2026-11-23 12:00:00", "0" * 64
    for datos in ("Pago de 100 pesos", "Pago de 900 pesos"):
        print(datos, "->", calcular_hash(1, fecha, datos, anterior))
def demostrar_registro():
    print(json.dumps(crear_registro(1, "Pago de 100 pesos", "0" * 64), ensure_ascii=False, indent=4))

def demostrar_encadenamiento():
    ejemplo = []
    for datos in ("Pago de 100 pesos", "Pago de 200 pesos", "Pago de 300 pesos"):
        agregar_a_cadena(ejemplo, datos)
    mostrar_registros(ejemplo)
    verificar_integridad(ejemplo)
    print("Demostracion temporal; no se guarda en el JSON.")

def mostrar_menu():
    print("\n=== MINI-BLOCKCHAIN ===")
    print("1. Agregar     2. Mostrar     3. Verificar     4. Alterar")
    print("5. Demo SHA    6. Demo registro    7. Demo cadena")
    print("8. Restaurar   0. Salir")

def main():
    print("Bienvenido a Mini-Blockchain")
    cadena = cargar_cadena()
    if cadena is None: return
    acciones = {"1": lambda: agregar_interactivo(cadena),
                "2": lambda: mostrar_registros(cadena),
                "3": lambda: verificar_integridad(cadena),
                "4": lambda: simular_alteracion(cadena),
                "5": demostrar_hash, "6": demostrar_registro,
                "7": demostrar_encadenamiento,
                "8": lambda: restaurar_cadena(cadena)}
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opcion: ").strip()
        if opcion == "0":
            print("Programa cerrado. Registros conservados en JSON.")
            break
        if opcion in acciones:
            acciones[opcion]()
        else:
            print("Opcion no valida.")

if __name__ == "__main__":
    main()
