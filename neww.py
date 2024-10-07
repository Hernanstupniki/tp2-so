import tkinter as tk
import random
import threading
import time

# Configuración de la memoria
MEMORIA_TOTAL = 1000  # Memoria total disponible (en MB)
MEMORIA_USADA = 0  # Memoria actualmente en uso (en MB)
TAMANO_PAGINA = 50  # Tamaño de cada página en MB
NUMERO_PAGINAS = MEMORIA_TOTAL // TAMANO_PAGINA  # Cantidad total de páginas en memoria
paginas_memoria = [None] * NUMERO_PAGINAS  # Tabla de páginas para la memoria

# Lista de procesos en diferentes estados
procesos = []
procesos_nuevos = []
procesos_listos = []
procesos_bloqueados = []
procesos_terminados = []
recursos_semaforos = [threading.Semaphore(1), threading.Semaphore(1), threading.Semaphore(1)]  # Semáforos para los recursos R0, R1, R2
proceso_ejecucion = None

# Clase para representar un proceso
class Proceso:
    def __init__(self, id, memoria):
        self.id = id
        self.memoria = memoria
        self.estado = 'Nuevos'
        self.veces_bloqueado = 0  # Atributo para contar las veces que ha sido bloqueado
        self.recurso = random.randint(0, 2)  # Asigna aleatoriamente R0, R1 o R2
        self.paginas = []  # Páginas asignadas en la memoria principal
        self.tiene_recurso = False  # Indica si este proceso tiene bloqueado un recurso

    def __str__(self):
        return f"Proceso {self.id}: {self.estado} (Memoria: {self.memoria} MB) Recurso: R{self.recurso}"

# Función para asignar páginas a un proceso en la memoria
def asignar_paginas(proceso):
    global MEMORIA_USADA
    paginas_necesarias = (proceso.memoria + TAMANO_PAGINA - 1) // TAMANO_PAGINA  # Redondeo hacia arriba

    if paginas_memoria.count(None) >= paginas_necesarias:
        for i in range(NUMERO_PAGINAS):
            if len(proceso.paginas) == paginas_necesarias:
                break
            if paginas_memoria[i] is None:
                paginas_memoria[i] = proceso.id
                proceso.paginas.append(i)
                MEMORIA_USADA += TAMANO_PAGINA

        return True
    else:
        return False

# Función para liberar las páginas asignadas a un proceso
def liberar_paginas(proceso):
    global MEMORIA_USADA
    for pagina in proceso.paginas:
        paginas_memoria[pagina] = None
        MEMORIA_USADA -= TAMANO_PAGINA
    proceso.paginas = []

# Función para agregar un proceso
def agregar_proceso(memoria_necesaria):
    proceso = Proceso(len(procesos) + 1, memoria_necesaria)

    if asignar_paginas(proceso):
        procesos_nuevos.append(proceso)
        proceso.estado = 'Nuevos'
        procesos.append(proceso)
    else:
        mensaje_error.config(text="Memoria insuficiente para el nuevo proceso.")

    actualizar_interfaz()

# Función para mover procesos de Nuevos a Listos
def nuevo_a_listo():
    while True:
        for proceso in procesos_nuevos[:]:
            if asignar_paginas(proceso):
                procesos_nuevos.remove(proceso)
                procesos_listos.append(proceso)
                proceso.estado = 'Listo'
                actualizar_interfaz()
        time.sleep(3)

# Función para manejar los procesos bloqueados y liberarlos cada 5 segundos
def revisar_procesos_bloqueados():
    while True:
        for proceso in procesos_bloqueados[:]:
            if proceso.tiene_recurso:  # Verifica si el proceso tenía un recurso bloqueado
                proceso.estado = 'Listo'
                procesos_bloqueados.remove(proceso)
                procesos_listos.append(proceso)
                mensaje_error.config(text=f"El Proceso {proceso.id} ha sido liberado del bloqueo.")
        actualizar_interfaz()
        time.sleep(5)  # Revisar cada 5 segundos

# Función para simular la ejecución de procesos
def ejecutar_procesos():
    global proceso_ejecucion
    while True:
        if procesos_listos:
            proceso_ejecucion = procesos_listos.pop(0)  # FIFO, obtenemos el primer proceso listo

            # Intentar adquirir el semáforo del recurso
            recurso_semaforo = recursos_semaforos[proceso_ejecucion.recurso]
            if recurso_semaforo.acquire(blocking=False):
                # Asignamos el recurso
                proceso_ejecucion.tiene_recurso = True  # Indica que tiene el recurso
                proceso_ejecucion.estado = 'Ejecutando'
                actualizar_interfaz()
                time.sleep(3)  # Simula el tiempo de ejecución del proceso

                # Simular que el proceso pasa por bloqueado al menos una vez
                if proceso_ejecucion.veces_bloqueado == 0:
                    proceso_ejecucion.veces_bloqueado += 1
                    proceso_ejecucion.estado = 'Bloqueado'
                    procesos_bloqueados.append(proceso_ejecucion)
                    mensaje_error.config(text=f"El Proceso {proceso_ejecucion.id} se ha bloqueado durante la ejecución.")
                else:
                    proceso_ejecucion.estado = 'Terminado'
                    liberar_paginas(proceso_ejecucion)
                    procesos_terminados.append(proceso_ejecucion)

                    # Liberar el recurso (semáforo) solo cuando el proceso ha terminado
                    recurso_semaforo.release()
                    proceso_ejecucion = None
            else:
                # Si el recurso está ocupado, el proceso se bloquea
                proceso_ejecucion.estado = 'Bloqueado'
                procesos_bloqueados.append(proceso_ejecucion)
                mensaje_error.config(text=f"El Proceso {proceso_ejecucion.id} se ha bloqueado porque el recurso R{proceso_ejecucion.recurso} está ocupado.")

        actualizar_interfaz()
        time.sleep(1)

# Función para agregar un proceso manualmente
def agregar_proceso_manual():
    try:
        memoria_necesaria = int(memoria_entry.get())
        if memoria_necesaria > 0:
            agregar_proceso(memoria_necesaria)
        else:
            tk.messagebox.showerror("Error", "La memoria debe ser un número positivo.")
    except ValueError:
        tk.messagebox.showerror("Error", "Ingrese un valor numérico válido para la memoria.")
    finally:
        memoria_entry.delete(0, tk.END)  # Limpiar el campo de entrada

# Función para agregar un proceso aleatorio
def agregar_proceso_aleatorio():
    memoria_necesaria = random.randint(50, 200)
    agregar_proceso(memoria_necesaria)

# Función para actualizar la interfaz gráfica
def actualizar_interfaz():
    memoria_label.config(text=f"Memoria Usada: {MEMORIA_USADA}/{MEMORIA_TOTAL} MB")

    # Limpiar y actualizar lista de procesos
    nuevos_listbox.delete(0, tk.END)
    for p in procesos_nuevos:
        nuevos_listbox.insert(tk.END, str(p))

    listos_listbox.delete(0, tk.END)
    for p in procesos_listos:
        listos_listbox.insert(tk.END, str(p))

    bloqueados_listbox.delete(0, tk.END)
    for p in procesos_bloqueados:
        bloqueados_listbox.insert(tk.END, str(p))

    terminados_listbox.delete(0, tk.END)
    for p in procesos_terminados:
        terminados_listbox.insert(tk.END, str(p))

    ejecucion_label.config(text=f"{proceso_ejecucion if proceso_ejecucion else ''}")
    mensaje_error.config(text="")  # Limpiar mensaje de error en cada actualización

    # Mostrar procesos en memoria
    mostrar_procesos_en_memoria()

    # Actualizar estado de los recursos
    actualizar_estado_recursos()

# Función para mostrar visualmente el uso de la memoria
def mostrar_procesos_en_memoria():
    # Limpiar el canvas
    canvas.delete("all")

    # Dibujar las páginas de memoria
    for i in range(NUMERO_PAGINAS):
        x0, y0 = (i % 10) * 50, (i // 10) * 50
        x1, y1 = x0 + 50, y0 + 50

        if paginas_memoria[i] is None:
            color = "white"
        else:
            color = "lightblue"

        canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
        canvas.create_text((x0 + 25, y0 + 25), text=str(paginas_memoria[i]) if paginas_memoria[i] is not None else "")

# Función para actualizar el estado de los recursos en la interfaz
def actualizar_estado_recursos():
    estado_recursos = []
    for i, semaforo in enumerate(recursos_semaforos):
        if semaforo._value == 1:
            estado_recursos.append(f"R{i}: Libre")
        else:
            estado_recursos.append(f"R{i}: Ocupado")

    recursos_label.config(text=" | ".join(estado_recursos))

# Configuración de la ventana principal
root = tk.Tk()
root.title("Gestión de Procesos")

# Elementos de la interfaz gráfica
memoria_label = tk.Label(root, text=f"Memoria Usada: {MEMORIA_USADA}/{MEMORIA_TOTAL} MB")
memoria_label.pack()

memoria_entry = tk.Entry(root)
memoria_entry.pack()

agregar_manual_button = tk.Button(root, text="Agregar Proceso Manualmente", command=agregar_proceso_manual)
agregar_manual_button.pack()

agregar_aleatorio_button = tk.Button(root, text="Agregar Proceso Aleatorio", command=agregar_proceso_aleatorio)
agregar_aleatorio_button.pack()

nuevos_listbox = tk.Listbox(root)
nuevos_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

listos_listbox = tk.Listbox(root)
listos_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

bloqueados_listbox = tk.Listbox(root)
bloqueados_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

terminados_listbox = tk.Listbox(root)
terminados_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

canvas = tk.Canvas(root, width=500, height=500)
canvas.pack()

ejecucion_label = tk.Label(root, text="")
ejecucion_label.pack()

mensaje_error = tk.Label(root, text="", fg="red")
mensaje_error.pack()

recursos_label = tk.Label(root, text="")
recursos_label.pack()

# Iniciar hilos para manejar los procesos
hilo_nuevo_a_listo = threading.Thread(target=nuevo_a_listo, daemon=True)
hilo_nuevo_a_listo.start()

hilo_ejecucion = threading.Thread(target=ejecutar_procesos, daemon=True)
hilo_ejecucion.start()

hilo_revisar_bloqueados = threading.Thread(target=revisar_procesos_bloqueados, daemon=True)
hilo_revisar_bloqueados.start()

root.mainloop()
