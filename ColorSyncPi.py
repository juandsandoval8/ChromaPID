import cv2
import tkinter as tk
from tkinter import ttk, filedialog, Scale
from PIL import Image, ImageTk
import threading
import time
import serial
import serial.tools.list_ports
import struct
import json

# Variables globales para CMYK y RGB
c_global, m_global, y_global, k_global = 0, 0, 0, 0
r_global, g_global, b_global = 0, 0, 0

# Variable para la conexión serial
ser = None
connected = False

def connect_to_serial():
    """Conecta con el dispositivo serial (Raspberry Pi Pico W)."""
    global ser, connected
    
    # Obtener lista de puertos disponibles
    ports = serial.tools.list_ports.comports()
    port_list = [port.device for port in ports]
    
    if not port_list:
        status_label.config(text="Error: No se encontraron puertos seriales")
        return False
    
    # Mostrar ventana de selección de puerto
    port_window = tk.Toplevel(window)
    port_window.title("Seleccionar Puerto")
    port_window.geometry("300x200")
    
    # Crear combobox para selección de puerto
    port_combo = ttk.Combobox(port_window, values=port_list)
    if port_list:
        port_combo.current(0)
    port_combo.pack(padx=20, pady=20)
    
    # Variable para almacenar el puerto seleccionado
    selected_port = [None]
    
    def on_select():
        selected_port[0] = port_combo.get()
        port_window.destroy()
    
    select_button = ttk.Button(port_window, text="Conectar", command=on_select)
    select_button.pack(pady=10)
    
    # Esperar a que la ventana se cierre
    window.wait_window(port_window)
    
    if not selected_port[0]:
        status_label.config(text="Error: No se seleccionó un puerto")
        return False
        
    try:
        # Intentar conectar al puerto seleccionado
        ser = serial.Serial(selected_port[0], 115200, timeout=1)
        time.sleep(2)  # Esperar a que la conexión se estabilice
        connected = True
        status_label.config(text=f"Conectado a {selected_port[0]}")
        return True
    except Exception as e:
        status_label.config(text=f"Error de conexión: {str(e)}")
        return False

def send_cmyk_values():
    """Envía los valores CMYK y RGB al Raspberry Pi Pico W."""
    global ser, connected, c_global, m_global, y_global, k_global, r_global, g_global, b_global
    
    if not connected or ser is None:
        status_label.config(text="Error: No hay conexión con el dispositivo")
        return False
    
    try:
        # Crear un diccionario con los valores
        data = {
            'c': c_global,
            'm': m_global,
            'y': y_global,
            'k': k_global,
            'r': r_global,
            'g': g_global,
            'b': b_global
        }
        
        # Convertir a JSON y enviar
        json_data = json.dumps(data) + '\n'
        ser.write(json_data.encode())
        
        # Esperar confirmación (opcional)
        response = ser.readline().decode().strip()
        if response == "OK":
            status_label.config(text="Valores enviados correctamente")
            return True
        else:
            status_label.config(text=f"Respuesta inesperada: {response}")
            return False
    except Exception as e:
        status_label.config(text=f"Error al enviar datos: {str(e)}")
        return False

def rgb_to_cmyk(r, g, b):
    """Convierte RGB a CMYK."""
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0
    k = 1 - max(r_norm, g_norm, b_norm)
    if k == 1:
        return 0, 0, 0, 100
    c = (1 - r_norm - k) / (1 - k)
    m = (1 - g_norm - k) / (1 - k)
    y = (1 - b_norm - k) / (1 - k)
    c_100 = int(c * 100)
    m_100 = int(m * 100)
    y_100 = int(y * 100)
    k_100 = int(k * 100)
    return c_100, m_100, y_100, k_100

def cmyk_to_rgb(c, m, y, k):
    """Convierte CMYK a RGB."""
    # Asegurarse de que los valores estén en el rango 0-100
    c = max(0, min(100, c))
    m = max(0, min(100, m))
    y = max(0, min(100, y))
    k = max(0, min(100, k))
    
    # Fórmula de conversión
    r = 255 * (1 - c/100) * (1 - k/100)
    g = 255 * (1 - m/100) * (1 - k/100)
    b = 255 * (1 - y/100) * (1 - k/100)
    
    return int(r), int(g), int(b)

def set_cmyk_values(c, m, y, k):
    """Actualiza variables globales, sliders de CMYK y valores RGB."""
    global c_global, m_global, y_global, k_global, r_global, g_global, b_global
    c_global, m_global, y_global, k_global = c, m, y, k
    
    # Calcular los valores RGB correspondientes
    r_global, g_global, b_global = cmyk_to_rgb(c, m, y, k)
    
    # Actualizar sliders si existen
    if 'c_slider' in globals():
        c_slider.set(c)
        m_slider.set(m)
        y_slider.set(y)
        k_slider.set(k)
    
    # Actualizar etiquetas
    actualizar_labels()
    
    # Enviar valores al dispositivo
    if connected:
        send_cmyk_values()

def mostrar_preview_color():
    """Muestra una previsualización del color CMYK seleccionado."""
    # Usar la función cmyk_to_rgb para convertir de CMYK a RGB
    r, g, b = cmyk_to_rgb(c_global, m_global, y_global, k_global)
    
    # Crear color hexadecimal para el widget
    hex_color = f'#{r:02x}{g:02x}{b:02x}'
    color_preview.config(bg=hex_color)

def guardar_valores():
    """Guarda los valores CMYK actuales y los envía al dispositivo."""
    status_label.config(text=f"Valores guardados: C:{c_global} M:{m_global} Y:{y_global} K:{k_global} | R:{r_global} G:{g_global} B:{b_global}")
    
    # Enviar valores al dispositivo
    if connected:
        send_cmyk_values()
    else:
        status_label.config(text="No hay conexión. Valores guardados localmente.")
    
    # Mostrar previsualización del color
    mostrar_preview_color()

def actualizar_labels():
    """Actualiza etiquetas con valores CMYK y RGB."""
    c_value_label.config(text=f"{c_global}")
    m_value_label.config(text=f"{m_global}")
    y_value_label.config(text=f"{y_global}")
    k_value_label.config(text=f"{k_global}")
    
    r_value_label.config(text=f"{r_global}")
    g_value_label.config(text=f"{g_global}")
    b_value_label.config(text=f"{b_global}")

def cargar_imagen():
    """Carga una imagen desde el sistema de archivos."""
    global image, photo
    
    file_path = filedialog.askopenfilename(
        filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")])
    
    if file_path:
        # Cargar imagen con OpenCV
        image = cv2.imread(file_path)
        # Convertir para mostrar en Tkinter
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        
        # Redimensionar manteniendo la relación de aspecto
        width, height = image_pil.size
        max_size = 400
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            image_pil = image_pil.resize((new_width, new_height), Image.LANCZOS)
            
            # También redimensionar la imagen de OpenCV para los clics
            image = cv2.resize(image, (new_width, new_height))
            
        photo = ImageTk.PhotoImage(image_pil)
        image_canvas.config(width=photo.width(), height=photo.height())
        image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        
        # Habilitar eventos de clic en el canvas
        image_canvas.bind("<Button-1>", on_image_click)
        
        # Actualizar estado
        status_label.config(text=f"Estado: Imagen cargada: {file_path.split('/')[-1]}")

def iniciar_camara():
    """Inicia la captura de la cámara."""
    global camera_active, cap
    
    if camera_active:
        # Si la cámara ya está activa, detenerla
        camera_active = False
        camera_button.config(text="Iniciar Cámara")
        if 'cap' in globals() and cap is not None:
            cap.release()
        return
    
    # Iniciar cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        status_label.config(text="Error: No se pudo acceder a la cámara")
        return
    
    camera_active = True
    camera_button.config(text="Detener Cámara")
    status_label.config(text="Estado: Cámara activa. Haz clic para capturar")
    
    # Iniciar hilo para mostrar video
    threading.Thread(target=mostrar_video, daemon=True).start()

def mostrar_video():
    """Muestra el video de la cámara en el canvas."""
    global cap, photo, image
    
    while camera_active:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Redimensionar frame
        height, width = frame.shape[:2]
        max_size = 400
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Convertir frame para Tkinter
        image = frame.copy()  # Guardar para detección de color
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(frame_pil)
        
        # Actualizar canvas
        image_canvas.config(width=photo.width(), height=photo.height())
        image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        
        time.sleep(0.03)  # ~30 FPS

def capturar_frame():
    """Captura un frame de la cámara."""
    global image
    
    if camera_active and 'cap' in globals() and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            image = frame.copy()
            # Mostrar el frame capturado
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(frame_pil)
            image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            status_label.config(text="Estado: Frame capturado")

def on_image_click(event):
    """Maneja clics en la imagen para detectar color."""
    if 'image' not in globals():
        return
        
    x, y = event.x, event.y
    
    # Verificar que las coordenadas estén dentro de la imagen
    if x < 0 or y < 0 or x >= image.shape[1] or y >= image.shape[0]:
        return
        
    # Obtener color RGB del pixel
    b, g, r = image[y, x]
    
    # Actualizar variables globales RGB
    global r_global, g_global, b_global
    r_global, g_global, b_global = r, g, b
    
    # Convertir a CMYK
    c, m, y, k = rgb_to_cmyk(r, g, b)
    
    # Actualizar valores globales y UI
    set_cmyk_values(c, m, y, k)
    
    # Mostrar color seleccionado usando RGB directo (el original clicado)
    color_preview.config(bg=f'rgb({r}, {g}, {b})')
    
    # Añadir marca en la imagen
    draw_image = image.copy()
    cv2.circle(draw_image, (x, y), 5, (0, 0, 255), -1)
    
    # Mostrar imagen con la marca
    draw_image_rgb = cv2.cvtColor(draw_image, cv2.COLOR_BGR2RGB)
    draw_image_pil = Image.fromarray(draw_image_rgb)
    photo_new = ImageTk.PhotoImage(draw_image_pil)
    image_canvas.create_image(0, 0, anchor=tk.NW, image=photo_new)
    global photo
    photo = photo_new
    
    status_label.config(text=f"Color seleccionado: RGB({r},{g},{b}) → CMYK({c},{m},{y},{k})")
    
    # Enviar valores al dispositivo
    if connected:
        send_cmyk_values()

def actualizar_desde_slider(c=None, m=None, y=None, k=None):
    """Actualiza los valores CMYK desde los sliders y recalcula RGB."""
    global c_global, m_global, y_global, k_global, r_global, g_global, b_global
    
    if c is not None:
        c_global = int(c)
    if m is not None:
        m_global = int(m)
    if y is not None:
        y_global = int(y)
    if k is not None:
        k_global = int(k)
    
    # Recalcular valores RGB
    r_global, g_global, b_global = cmyk_to_rgb(c_global, m_global, y_global, k_global)
    
    actualizar_labels()
    mostrar_preview_color()

def setup_gui():
    """Configura la interfaz gráfica."""
    global window, image_canvas, status_label, c_slider, m_slider, y_slider, k_slider
    global c_value_label, m_value_label, y_value_label, k_value_label, color_preview
    global r_value_label, g_value_label, b_value_label
    global camera_button, camera_active
    
    window = tk.Tk()
    window.title("Controlador CMYK y RGB para Raspberry Pi Pico W")
    window.geometry("900x650")
    
    camera_active = False
    
    # Panel izquierdo para la imagen
    left_frame = ttk.Frame(window)
    left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=5, pady=5)
    
    # Canvas para mostrar imagen
    image_frame = ttk.LabelFrame(left_frame, text="Imagen")
    image_frame.pack(fill='both', expand=True, padx=5, pady=5)
    
    image_canvas = tk.Canvas(image_frame, width=400, height=300, bg='lightgray')
    image_canvas.pack(padx=5, pady=5)
    
    # Botones de control de imagen
    image_buttons_frame = ttk.Frame(left_frame)
    image_buttons_frame.pack(fill='x', padx=5, pady=5)
    
    load_button = ttk.Button(image_buttons_frame, text="Cargar Imagen", command=cargar_imagen)
    load_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    camera_button = ttk.Button(image_buttons_frame, text="Iniciar Cámara", command=iniciar_camara)
    camera_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    capture_button = ttk.Button(image_buttons_frame, text="Capturar", command=capturar_frame)
    capture_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    connect_button = ttk.Button(image_buttons_frame, text="Conectar", command=connect_to_serial)
    connect_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    # Panel derecho para controles CMYK y RGB
    right_frame = ttk.Frame(window)
    right_frame.pack(side=tk.RIGHT, fill='both', padx=5, pady=5)
    
    # Marco para controles CMYK
    cmyk_frame = ttk.LabelFrame(right_frame, text="Control CMYK")
    cmyk_frame.pack(fill='both', expand=True, padx=5, pady=5)
    
    # Previsualización de color
    preview_frame = ttk.Frame(cmyk_frame)
    preview_frame.pack(fill='x', padx=5, pady=5)
    
    ttk.Label(preview_frame, text="Color:").pack(side=tk.LEFT, padx=5, pady=5)
    color_preview = tk.Label(preview_frame, width=10, height=2, bg='white', relief='solid', borderwidth=1)
    color_preview.pack(side=tk.LEFT, padx=5, pady=5)
    
    # Sliders CMYK
    c_frame = ttk.Frame(cmyk_frame)
    c_frame.pack(fill='x', padx=5, pady=2)
    ttk.Label(c_frame, text="C:", width=2).pack(side=tk.LEFT, padx=5)
    c_slider = Scale(c_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                     command=lambda val: actualizar_desde_slider(c=val))
    c_slider.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
    c_value_label = ttk.Label(c_frame, text="0", width=3)
    c_value_label.pack(side=tk.LEFT, padx=5)
    
    m_frame = ttk.Frame(cmyk_frame)
    m_frame.pack(fill='x', padx=5, pady=2)
    ttk.Label(m_frame, text="M:", width=2).pack(side=tk.LEFT, padx=5)
    m_slider = Scale(m_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                     command=lambda val: actualizar_desde_slider(m=val))
    m_slider.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
    m_value_label = ttk.Label(m_frame, text="0", width=3)
    m_value_label.pack(side=tk.LEFT, padx=5)
    
    y_frame = ttk.Frame(cmyk_frame)
    y_frame.pack(fill='x', padx=5, pady=2)
    ttk.Label(y_frame, text="Y:", width=2).pack(side=tk.LEFT, padx=5)
    y_slider = Scale(y_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                     command=lambda val: actualizar_desde_slider(y=val))
    y_slider.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
    y_value_label = ttk.Label(y_frame, text="0", width=3)
    y_value_label.pack(side=tk.LEFT, padx=5)
    
    k_frame = ttk.Frame(cmyk_frame)
    k_frame.pack(fill='x', padx=5, pady=2)
    ttk.Label(k_frame, text="K:", width=2).pack(side=tk.LEFT, padx=5)
    k_slider = Scale(k_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                     command=lambda val: actualizar_desde_slider(k=val))
    k_slider.pack(side=tk.LEFT, fill='x', expand=True, padx=5)
    k_value_label = ttk.Label(k_frame, text="0", width=3)
    k_value_label.pack(side=tk.LEFT, padx=5)
    
    # Marco para valores RGB
    rgb_frame = ttk.LabelFrame(right_frame, text="Valores RGB")
    rgb_frame.pack(fill='x', padx=5, pady=5)
    
    r_frame = ttk.Frame(rgb_frame)
    r_frame.pack(fill='x', padx=5, pady=2)
    ttk.Label(r_frame, text="R:", width=2).pack(side=tk.LEFT, padx=5)
    r_value_label = ttk.Label(r_frame, text="0", width=3)
    r_value_label.pack(side=tk.LEFT, padx=5)
    
    g_frame = ttk.Frame(rgb_frame)
    g_frame.pack(fill='x', padx=5, pady=2)
    ttk.Label(g_frame, text="G:", width=2).pack(side=tk.LEFT, padx=5)
    g_value_label = ttk.Label(g_frame, text="0", width=3)
    g_value_label.pack(side=tk.LEFT, padx=5)
    
    b_frame = ttk.Frame(rgb_frame)
    b_frame.pack(fill='x', padx=5, pady=2)
    ttk.Label(b_frame, text="B:", width=2).pack(side=tk.LEFT, padx=5)
    b_value_label = ttk.Label(b_frame, text="0", width=3)
    b_value_label.pack(side=tk.LEFT, padx=5)
    
    # Botón para enviar valores
    send_button = ttk.Button(right_frame, text="Enviar a Raspberry Pi", command=send_cmyk_values)
    send_button.pack(pady=5)
    
    # Historial de colores guardados
    history_frame = ttk.LabelFrame(right_frame, text="Historial de Colores")
    history_frame.pack(fill='both', expand=True, padx=5, pady=5)
    
    history_listbox = tk.Listbox(history_frame, height=6)
    history_listbox.pack(fill='both', expand=True, padx=5, pady=5)
    
    def guardar_en_historial():
        """Guarda el color actual en el historial."""
        # Formatear texto para mostrar en el historial
        entry = f"C:{c_global} M:{m_global} Y:{y_global} K:{k_global} - RGB({r_global},{g_global},{b_global})"
        history_listbox.insert(0, entry)
        status_label.config(text=f"Color guardado en historial: {entry}")
    
    def aplicar_desde_historial(event):
        """Aplica un color seleccionado del historial."""
        selection = history_listbox.curselection()
        if selection:
            entry = history_listbox.get(selection[0])
            # Parsear la entrada para obtener valores CMYK
            try:
                cmyk_part = entry.split('-')[0].strip()
                c = int(cmyk_part.split('C:')[1].split()[0])
                m = int(cmyk_part.split('M:')[1].split()[0])
                y = int(cmyk_part.split('Y:')[1].split()[0])
                k = int(cmyk_part.split('K:')[1].split()[0])
                set_cmyk_values(c, m, y, k)
                status_label.config(text=f"Color aplicado del historial: {entry}")
            except Exception as e:
                status_label.config(text=f"Error al aplicar color: {str(e)}")
    
    history_listbox.bind("<Double-1>", aplicar_desde_historial)
    
    add_to_history_button = ttk.Button(history_frame, text="Añadir a Historial", command=guardar_en_historial)
    add_to_history_button.pack(pady=5)
    
    # Barra de estado
    status_frame = ttk.Frame(window)
    status_frame.pack(fill='x', side=tk.BOTTOM, padx=5, pady=5)
    
    status_label = ttk.Label(status_frame, text="Estado: Desconectado. Usa el botón 'Conectar' para conectar con el Raspberry Pi Pico", relief=tk.SUNKEN, anchor=tk.W)
    status_label.pack(fill='x')
    
    # Iniciar actualización de etiquetas
    actualizar_labels()

def main():
    """Función principal."""
    # Inicializar la interfaz gráfica
    setup_gui()
    
    # Iniciar el bucle principal de Tkinter
    window.mainloop()
    
    # Limpieza al salir
    if 'cap' in globals() and cap is not None:
        cap.release()
    
    if 'ser' in globals() and ser is not None:
        ser.close()

if __name__ == "__main__":
    main()
