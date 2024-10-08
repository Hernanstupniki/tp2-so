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
procesos_ocupando_recurso = [None, None, None]  # Lista para rastrear qué proceso tiene cada recurso
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
        self.esperando_recurso = False
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

# Función para manejar los procesos bloqueados y liberarlos
def revisar_procesos_bloqueados():
    while True:
        for proceso in procesos_bloqueados[:]:
            recurso_semaforo = recursos_semaforos[proceso.recurso]

            if proceso.tiene_recurso:
                # Si el proceso ya tiene el recurso asignado, se libera el recurso y se mantiene bloqueado
                recurso_semaforo.release()
                mensaje_error.config(text=f"El Proceso {proceso.id} ha liberado el recurso R{proceso.recurso} pero sigue bloqueado.")
            else:
                # Si el recurso está libre y el proceso estaba esperando, se mueve a listos
                if recurso_semaforo._value == 1 and proceso.esperando_recurso:
                    proceso.estado = 'Listo'
                    procesos_bloqueados.remove(proceso)
                    procesos_listos.append(proceso)
                    proceso.esperando_recurso = False  # <-- Reiniciar el flag
                    mensaje_error.config(text=f"El Proceso {proceso.id} ha sido liberado porque el recurso R{proceso.recurso} está libre.")
                else:
                    mensaje_error.config(text=f"El Proceso {proceso.id} sigue bloqueado porque el recurso R{proceso.recurso} está ocupado.")
        
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
                procesos_ocupando_recurso[proceso_ejecucion.recurso] = proceso_ejecucion.id  # Asigna el proceso al recurso
                proceso_ejecucion.estado = 'Ejecutando'
                actualizar_interfaz()
                time.sleep(3)  # Simula el tiempo de ejecución del proceso

                # Simular el ciclo de bloqueo solo si el proceso no ha alcanzado el límite de bloqueos
                if proceso_ejecucion.veces_bloqueado < 3:
                    proceso_ejecucion.veces_bloqueado += 1
                    proceso_ejecucion.estado = 'Bloqueado'
                    procesos_bloqueados.append(proceso_ejecucion)
                    proceso_ejecucion.esperando_recurso = True  # <-- Nuevo
                    mensaje_error.config(text=f"El Proceso {proceso_ejecucion.id} se ha bloqueado (bloqueo {proceso_ejecucion.veces_bloqueado}/3).")
                else:
                    # Si ha alcanzado 3 veces bloqueado, pasa a terminado
                    proceso_ejecucion.estado = 'Terminado'
                    liberar_paginas(proceso_ejecucion)
                    procesos_terminados.append(proceso_ejecucion)
                    mensaje_error.config(text=f"El Proceso {proceso_ejecucion.id} ha terminado después de 3 bloqueos.")
                    recurso_semaforo.release()  # Liberar el recurso

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
    canvas.delete("all")  # Limpiar el canvas
    for i in range(NUMERO_PAGINAS):
        x0 = (i % 10) * 50
        y0 = (i // 10) * 50
        x1 = x0 + 50
        y1 = y0 + 50
        if paginas_memoria[i] is not None:
            color = "lightblue"
            canvas.create_rectangle(x0, y0, x1, y1, fill=color)
            canvas.create_text((x0 + 25, y0 + 25), text=paginas_memoria[i])
        else:
            canvas.create_rectangle(x0, y0, x1, y1, outline="black")

# Función para actualizar el estado de los recursos
def actualizar_estado_recursos():
    for i, recurso in enumerate(["R0", "R1", "R2"]):
        estado = f"{recurso}: {'Libre' if procesos_ocupando_recurso[i] is None else f'Ocupado por P{procesos_ocupando_recurso[i]}'}"
        recurso_labels[i].config(text=estado)

# Configuración de la interfaz gráfica
ventana = tk.Tk()
ventana.title("Simulación de Procesos y Memoria")

# Widgets de memoria y procesos
memoria_label = tk.Label(ventana, text=f"Memoria Usada: {MEMORIA_USADA}/{MEMORIA_TOTAL} MB")
memoria_label.pack()

canvas = tk.Canvas(ventana, width=500, height=300, bg="white")
canvas.pack()

nuevos_frame = tk.Frame(ventana)
nuevos_frame.pack(side=tk.LEFT, padx=10)
nuevos_label = tk.Label(nuevos_frame, text="Nuevos")
nuevos_label.pack()
nuevos_listbox = tk.Listbox(nuevos_frame, width=30, height=10)
nuevos_listbox.pack()

listos_frame = tk.Frame(ventana)
listos_frame.pack(side=tk.LEFT, padx=10)
listos_label = tk.Label(listos_frame, text="Listos")
listos_label.pack()
listos_listbox = tk.Listbox(listos_frame, width=30, height=10)
listos_listbox.pack()

bloqueados_frame = tk.Frame(ventana)
bloqueados_frame.pack(side=tk.LEFT, padx=10)
bloqueados_label = tk.Label(bloqueados_frame, text="Bloqueados")
bloqueados_label.pack()
bloqueados_listbox = tk.Listbox(bloqueados_frame, width=30, height=10)
bloqueados_listbox.pack()

terminados_frame = tk.Frame(ventana)
terminados_frame.pack(side=tk.LEFT, padx=10)
terminados_label = tk.Label(terminados_frame, text="Terminados")
terminados_label.pack()
terminados_listbox = tk.Listbox(terminados_frame, width=30, height=10)
terminados_listbox.pack()

# Entrada y botones para agregar procesos
memoria_entry = tk.Entry(ventana)
memoria_entry.pack(pady=10)
agregar_manual_button = tk.Button(ventana, text="Agregar Proceso Manual", command=agregar_proceso_manual)
agregar_manual_button.pack(pady=5)

agregar_aleatorio_button = tk.Button(ventana, text="Agregar Proceso Aleatorio", command=agregar_proceso_aleatorio)
agregar_aleatorio_button.pack(pady=5)

# Estado de ejecución y mensajes
ejecucion_label = tk.Label(ventana, text="")
ejecucion_label.pack(pady=10)
mensaje_error = tk.Label(ventana, text="", fg="red")
mensaje_error.pack()

# Estado de los recursos
recurso_labels = []
for i in range(3):
    label = tk.Label(ventana, text=f"R{i}: Libre")
    label.pack()
    recurso_labels.append(label)

# Iniciar los hilos para simular los procesos
threading.Thread(target=nuevo_a_listo, daemon=True).start()
threading.Thread(target=revisar_procesos_bloqueados, daemon=True).start()
threading.Thread(target=ejecutar_procesos, daemon=True).start()

# Ejecutar la ventana de la interfaz gráfica
ventana.mainloop()
