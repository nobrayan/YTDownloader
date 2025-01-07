"""

    @nobrayan

"""

import os
import threading
from tkinter import Tk, Entry, Button, StringVar, filedialog, messagebox, ttk
from yt_dlp import YoutubeDL
import subprocess

# Variables globales para control de descarga
cancelar_event = threading.Event()
formatos_disponibles = []  # Almacenaremos los formatos disponibles globalmente

def seleccionar_ruta():
    ruta = filedialog.askdirectory()
    if ruta:
        ruta_var.set(ruta)

def obtener_titulo_original(url):
    try:
        ydl_opts = {'quiet': True, 'format': 'best'}
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict.get("title", "Untitled")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo obtener el título del video: {e}")
        return "Untitled"

def listar_formatos():
    url = url_var.get()
    if not url:
        messagebox.showerror("Error", "Por favor, ingresa el enlace del video.")
        return

    try:
        ydl_opts = {'quiet': True, 'listformats': True}  # Activar la opción de listar formatos
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            
            # Crear una lista con los formatos disponibles
            global formatos_disponibles
            formatos_disponibles = []
            for f in formats:
                tipo = ""
                calidad = ""
                formato_archivo = f.get('ext', 'Desconocido')  # Obtener el formato (extensión)
                tamano = f.get('filesize', 0)  # Tamaño en bytes
                tamano_str = "Desconocido"
                
                # Verificar que tamaño no sea None y convertirlo a tamaño legible
                if tamano and tamano > 0:
                    tamano_gb = tamano / (1024 * 1024 * 1024)  # Convertir a GiB
                    if tamano_gb >= 1:
                        tamano_str = f"{tamano_gb:.2f} GiB"
                    else:
                        tamano_mb = tamano / (1024 * 1024)  # Convertir a MB
                        tamano_str = f"{tamano_mb:.2f} MB"

                if f.get('acodec') != 'none' and f.get('vcodec') != 'none':  # Si tiene audio y video
                    tipo = "Audio y Video"
                    calidad = str(f.get('height', 'Desconocido')) + "p"  # Convertir a cadena antes de concatenar
                elif f.get('acodec') != 'none':  # Si es solo audio
                    tipo = "Audio"
                    calidad = f.get('acodec', 'Desconocido')  # Código de audio
                elif f.get('vcodec') != 'none':  # Si es solo video
                    tipo = "Video"
                    calidad = str(f.get('height', 'Desconocido')) + "p"  # Convertir a cadena antes de concatenar
                
                formato = f"{f.get('format_id')} {tipo} {calidad} {formato_archivo}"  # Formato final
                formatos_disponibles.append({'description': formato, 'format_id': f.get('format_id')})
            
            # Actualizar el título con el título original del video
            titulo_var.set(obtener_titulo_original(url))  
            
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron listar los formatos: {e}")

def descargar_video():
    """Función para manejar la descarga del video."""
    global cancelar_event
    try:
        url = url_var.get()
        calidad_opcion = calidad_var.get()  # Tomamos la opción seleccionada
        titulo = titulo_var.get().strip()

        # Si el campo está vacío o contiene el texto predeterminado, usar el título original
        if titulo == "" or titulo == "Nombre del archivo (opcional)":
            titulo = obtener_titulo_original(url)

        ruta = ruta_var.get()

        if not url:
            messagebox.showerror("Error", "Por favor, ingresa el enlace del video.")
            return

        if not ruta:
            # Si no se ha seleccionado una ruta, usar la ruta del archivo ejecutable
            ruta = os.path.dirname(os.path.abspath(__file__))
            ruta_var.set(ruta)

        # Obtener el formato seleccionado
        formato_seleccionado = None
        tipo_archivo = ""
        if calidad_opcion == "Mejor Calidad":
            formato_seleccionado = "bestvideo+bestaudio/best"
            tipo_archivo = "Video con Audio"
        elif calidad_opcion == "Peor Calidad":
            formato_seleccionado = "worstvideo+worstaudio/worst"
            tipo_archivo = "Video con Audio"
        elif calidad_opcion == "Mejor Calidad de Audio":
            formato_seleccionado = "bestaudio"
            tipo_archivo = "Audio"
        elif calidad_opcion == "Peor Calidad de Audio":
            formato_seleccionado = "worstaudio"
            tipo_archivo = "Audio"
        elif calidad_opcion == "Mejor Calidad de Video":
            formato_seleccionado = "bestvideo"
            tipo_archivo = "Video"
        elif calidad_opcion == "Peor Calidad de Video":
            formato_seleccionado = "worstvideo"
            tipo_archivo = "Video"
        elif calidad_opcion in ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]:
            # Intentar descargar un video con la calidad específica seleccionada
            formato_seleccionado = f"bestvideo[height={calidad_opcion[:-1]}]+bestaudio/best[height={calidad_opcion[:-1]}]"
            tipo_archivo = "Video con Audio"

        # Verificar si el formato seleccionado es válido
        if not formato_seleccionado:
            messagebox.showerror("Error", "Opción de calidad no válida.")
            return

        # Nombre del archivo con el formato
        nombre_archivo = f"{titulo} ({calidad_opcion})"
        
        # Configuración de opciones para yt-dlp
        ydl_opts = {
            'format': formato_seleccionado,  # Usar el formato de calidad seleccionado
            'outtmpl': os.path.join(ruta, f"{nombre_archivo}.%(ext)s"),  # Nombre del archivo
            'quiet': False,  # Para ver la salida de yt-dlp
            'merge_output_format': 'mp4',  # Unión rápida en formato MP4
            'postprocessor_args': [
                '-c:v', 'copy',  # No recodificar video
                '-c:a', 'aac',   # Codificar audio solo si es necesario
                '-preset', 'ultrafast',  # Usar preset más rápido
                '-threads', '4'  # Usar 4 hilos para procesamiento (ajustar según tu CPU)
            ],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Salida en MP4
            }],
        }

        # Función para manejar el progreso
        def my_hook(d):
            if cancelar_event.is_set():
                raise Exception("Descarga cancelada")
            if d['status'] == 'downloading':
                if d.get('total_bytes') is not None:
                    porcentaje = d['downloaded_bytes'] / d['total_bytes'] * 100 if d['total_bytes'] > 0 else 0
                    barra_progreso['value'] = porcentaje
                    ventana.update_idletasks()  # Actualizar la ventana

        ydl_opts['progress_hooks'] = [my_hook]

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            if "Requested format is not available" in str(e):
                messagebox.showerror("Error", "Calidad no disponible.")
            else:
                messagebox.showerror("Error", f"Se produjo un error: {e}")
            return

        messagebox.showinfo("Éxito", "¡Descarga completada!")
    except Exception as e:
        messagebox.showerror("Error", f"Se produjo un error: {e}")
    finally:
        cancelar_event.clear()
        boton_descargar.config(text="Descargar", command=iniciar_descarga, bg="#4CAF50")  # Botón verde
        barra_progreso['value'] = 0  # Resetear la barra de progreso

# Función para convertir el video
def convertir_video():
    archivo = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.webm *.mkv")])
    if archivo:
        try:
            # Obtener la calidad seleccionada desde el combobox
            compresion_seleccionada = compresion_var.get()
            
            # Mapear las opciones de calidad a valores de CRF
            if compresion_seleccionada == "A":
                crf_valor = "18"  # Alta calidad
                crf_opcion = True
            elif compresion_seleccionada == "M":
                crf_valor = "23"  # Calidad estándar
                crf_opcion = True
            elif compresion_seleccionada == "B":
                crf_valor = "28"  # Baja calidad
                crf_opcion = True
            elif compresion_seleccionada == "O":
                crf_opcion = False  # Mantener calidad original
            else:
                crf_valor = "23"  # Valor por defecto (media calidad)
                crf_opcion = True
            
            # Nombre del archivo de salida con el sufijo correspondiente según la compresión seleccionada
            nombre_salida = f"{os.path.splitext(os.path.basename(archivo))[0]} (Convertido"
            if compresion_seleccionada == "A":
                nombre_salida += f" Alta"
            elif compresion_seleccionada == "M":
                nombre_salida += f" Media"
            elif compresion_seleccionada == "B":
                nombre_salida += f" Baja"
            nombre_salida += ").mp4"
            
            ruta_salida = os.path.join(os.path.dirname(archivo), nombre_salida)
            
            # Comando para convertir el video usando FFmpeg con la calidad seleccionada
            comando = [
                'ffmpeg', '-i', archivo,  # Entrada
                '-c:v', 'libx264',  # Códec de video H.264
                '-c:a', 'aac',  # Códec de audio AAC
                '-strict', 'experimental',  # Para habilitar el códec experimental
            ]
            
            # Si se seleccionó "Original", no se utiliza CRF
            if crf_opcion:
                comando.extend(['-crf', crf_valor])  # Calidad ajustada
            
            comando.append(ruta_salida)  # Salida

            subprocess.run(comando, check=True)
            messagebox.showinfo("Éxito", f"El video ha sido convertido y guardado como {ruta_salida}.")
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error al convertir el video: {e}")

def iniciar_descarga():
    global cancelar_event
    cancelar_event.clear()  # Restablecer la señal de cancelación
    threading.Thread(target=descargar_video, daemon=True).start()
    boton_descargar.config(text="Cancelar", command=cancelar_descarga, bg="#FF4C4C")  # Color rojo para cancelar

def cancelar_descarga():
    cancelar_event.set()  # Establece la señal de cancelación
    boton_descargar.config(text="Descargar", command=iniciar_descarga, bg="#4CAF50")  # Restaurar el botón y color

def on_focus_in(event, placeholder, entry):
    if entry.get() == placeholder:
        entry.delete(0, "end")
        entry.config(fg="white")  # Cambiar el color del texto a blanco

def on_focus_out(event, placeholder, entry):
    if entry.get() == "":
        entry.insert(0, placeholder)
        entry.config(fg="grey")  # Cambiar el color del texto a gris tenue

# Configuración de la ventana principal
ventana = Tk()
ventana.title("Descargador YouTube")
ventana.geometry("300x275")  # Ventana
ventana.config(bg="#2e2e2e")

# Configuración del grid
ventana.grid_rowconfigure(0, weight=1)
ventana.grid_rowconfigure(1, weight=1)
ventana.grid_rowconfigure(2, weight=1)
ventana.grid_rowconfigure(3, weight=1)
ventana.grid_rowconfigure(4, weight=1)
ventana.grid_rowconfigure(5, weight=1)

ventana.grid_columnconfigure(0, weight=19)  # Caja de entrada con 95% de espacio
ventana.grid_columnconfigure(1, weight=1)   # Botón con 5% de espacio

# Variables
url_var = StringVar()
calidad_var = StringVar()
titulo_var = StringVar()
ruta_var = StringVar()
compresion_var = StringVar()

# Estilo de entrada (background y texto)
entry_style = {"bg": "#3a3a3a", "fg": "grey", "insertbackground": "white", "borderwidth": 1, "relief": "solid", "font": ("Segoe UI", 10)}

# Enlace del video
url_entry = Entry(ventana, textvariable=url_var, width=20, **entry_style)
url_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")  # Margen de 5px
url_entry.insert(0, "Ingresa el enlace del video")
url_entry.bind("<FocusIn>", lambda event: on_focus_in(event, "Ingresa el enlace del video", url_entry))
url_entry.bind("<FocusOut>", lambda event: on_focus_out(event, "Ingresa el enlace del video", url_entry))

# Botón para listar formatos y mostrarlos en la consola
Button(ventana, text="?", command=lambda: listar_formatos() if url_var.get().strip() and url_var.get().strip() != "Ingresa el enlace del video" else messagebox.showerror("Error", "Por favor, ingresa el enlace del video."), bg="#4CAF50", fg="white", relief="flat", activebackground="#888", activeforeground="white").grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# Combobox para seleccionar la calidad
calidad_opciones = [
    "Mejor Calidad",  # Mejor calidad (audio y video combinados)
    "Mejor Calidad de Video",  # Mejor calidad de solo video
    "Mejor Calidad de Audio",  # Mejor calidad de solo audio
    "Peor Calidad",  # Peor calidad (audio y video combinados)
    "Peor Calidad de Video",  # Peor calidad de solo video
    "Peor Calidad de Audio",  # Peor calidad de solo audio
    "2160p",  # Video 2160p (4K) con audio combinado
    "1440p",  # Video 1440p (2K) con audio combinado
    "1080p",  # Video 1080p con audio combinado
    "720p",  # Video 720p con audio combinado
    "480p",  # Video 480p con audio combinado
    "360p",  # Video 360p con audio combinado
    "240p",  # Video 240p con audio combinado
    "144p"  # Video 144p con audio combinado
]
calidad_combo = ttk.Combobox(ventana, textvariable=calidad_var, values=calidad_opciones, state="readonly")
calidad_combo.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
calidad_combo.set("Mejor Calidad")  # Valor predeterminado

# Título del archivo
titulo_entry = Entry(ventana, textvariable=titulo_var, width=20, **entry_style)
titulo_entry.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")  # Margen de 5px
titulo_entry.insert(0, "Nombre del archivo (opcional)")
titulo_entry.bind("<FocusIn>", lambda event: on_focus_in(event, "Nombre del archivo (opcional)", titulo_entry))
titulo_entry.bind("<FocusOut>", lambda event: on_focus_out(event, "Nombre del archivo (opcional)", titulo_entry))

# Ruta de descarga
ruta_entry = Entry(ventana, textvariable=ruta_var, width=20, **entry_style)
ruta_entry.grid(row=3, column=0, padx=5, pady=5, sticky="ew")  # Margen de 5px
ruta_entry.insert(0, "")
ruta_entry.bind("<FocusIn>", lambda event: on_focus_in(event, " ", ruta_entry))
ruta_entry.bind("<FocusOut>", lambda event: on_focus_out(event, " ", ruta_entry))

# Botón para seleccionar la carpeta de descarga
Button(ventana, text="...", command=seleccionar_ruta, bg="#444", fg="white", relief="flat", activebackground="#888", activeforeground="white").grid(row=3, column=1, padx=5, pady=5, sticky="ew")  # Margen de 5px

# Barra de progreso
barra_progreso = ttk.Progressbar(ventana, orient="horizontal", length=280, mode="determinate")
barra_progreso.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Botón Descargar (inicia la descarga)
boton_descargar = Button(ventana, text="Descargar", command=iniciar_descarga, bg="#4CAF50", fg="white", relief="flat", activebackground="#888", activeforeground="white")
boton_descargar.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Botón para convertir video
boton_convertir = Button(ventana, text="Convertir Video", command=convertir_video, bg="#FFA500", fg="white", relief="flat", activebackground="#888", activeforeground="white")
boton_convertir.grid(row=6, column=0, padx=5, pady=5, sticky="ew")

# Combobox para seleccionar la compresión
compresion_opciones = [
    "O",  # Mantener calidad original
    "A",  # Calidad Alta
    "M",  # Calidad Media
    "B"  # Calidad Baja
]
compresion_var.set("O")  # Valor predeterminado
compresion_combo = ttk.Combobox(ventana, textvariable=compresion_var, values=compresion_opciones, state="readonly", width=1)
compresion_combo.grid(row=6, column=1, padx=2, pady=2, sticky="ew")

# Ejecutar la ventana
ventana.mainloop()

