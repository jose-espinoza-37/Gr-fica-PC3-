import tkinter as tk
from tkinter import filedialog, messagebox
from pydub import AudioSegment
from pathlib import Path


class DivisorAudio:

    def __init__(self, root):

        self.root = root
        self.root.title("Divisor de Audio MP3")
        self.root.geometry("640x580")
        self.root.resizable(False, False)

        self.archivo = None
        self.carpeta_salida = None
        self.duracion_audio = None

        # Título
        tk.Label(
            root,
            text="DIVISOR DE AUDIO MP3",
            font=("Arial", 17, "bold")
        ).pack(pady=15)

        # Selección del archivo
        tk.Button(
            root,
            text="Seleccionar archivo MP3",
            command=self.seleccionar_archivo,
            width=30
        ).pack(pady=5)

        self.label_archivo = tk.Label(
            root,
            text="Ningún archivo seleccionado",
            wraplength=480
        )
        self.label_archivo.pack(pady=5)

        self.label_duracion = tk.Label(
            root,
            text="Duración: --"
        )
        self.label_duracion.pack(pady=5)

        # Parámetros de segmentación
        frame = tk.LabelFrame(
            root,
            text="Configuración de los segmentos",
            padx=15,
            pady=10
        )
        frame.pack(padx=25, pady=15, fill="x")

        # Duración del clip
        tk.Label(
            frame,
            text="Duración de cada clip (segundos):"
        ).grid(row=0, column=0, sticky="w", pady=8)

        self.entrada_duracion = tk.Entry(
            frame,
            width=12,
            justify="center"
        )
        self.entrada_duracion.insert(0, "30")
        self.entrada_duracion.grid(row=0, column=1, padx=10)

        # Distancia entre clips
        tk.Label(
            frame,
            text="Distancia entre clips (segundos):"
        ).grid(row=1, column=0, sticky="w", pady=8)

        self.entrada_distancia = tk.Entry(
            frame,
            width=12,
            justify="center"
        )
        self.entrada_distancia.insert(0, "15")
        self.entrada_distancia.grid(row=1, column=1, padx=10)

        # Segundo inicial
        tk.Label(
            frame,
            text="Segundo inicial:"
        ).grid(row=2, column=0, sticky="w", pady=8)

        self.entrada_inicio = tk.Entry(
            frame,
            width=12,
            justify="center"
        )
        self.entrada_inicio.insert(0, "0")
        self.entrada_inicio.grid(row=2, column=1, padx=10)

        # Información de la configuración
        self.label_solapamiento = tk.Label(
            frame,
            text="Solapamiento: 15 segundos",
            fg="#176B87",
            font=("Arial", 9, "bold")
        )
        self.label_solapamiento.grid(
            row=3,
            column=0,
            columnspan=2,
            pady=8
        )

        # Actualizar información al modificar valores
        self.entrada_duracion.bind(
            "<KeyRelease>",
            self.actualizar_solapamiento
        )

        self.entrada_distancia.bind(
            "<KeyRelease>",
            self.actualizar_solapamiento
        )

        # Carpeta de destino
        tk.Button(
            root,
            text="Seleccionar carpeta de destino",
            command=self.seleccionar_carpeta,
            width=30
        ).pack(pady=5)

        self.label_carpeta = tk.Label(
            root,
            text="Destino: carpeta del MP3",
            wraplength=480
        )
        self.label_carpeta.pack(pady=5)

        # Información de cantidad de clips
        self.label_cantidad = tk.Label(
            root,
            text="Clips que se generarán: --",
            font=("Arial", 10, "bold")
        )
        self.label_cantidad.pack(pady=8)

        # Botón de ejecución
        tk.Button(
            root,
            text="DIVIDIR AUDIO",
            command=self.dividir_audio,
            bg="#176B87",
            fg="white",
            font=("Arial", 11, "bold"),
            width=30,
            height=2
        ).pack(pady=10)

        # Botón para finalizar
        tk.Button(
            root,
            text="FINALIZAR",
            command=self.root.destroy,
            bg="#B23A48",
            fg="white",
            font=("Arial", 10, "bold"),
            width=30,
            height=2
        ).pack(pady=5)

    def seleccionar_archivo(self):

        archivo = filedialog.askopenfilename(
            title="Seleccionar audio",
            filetypes=[("Archivos MP3", "*.mp3")]
        )

        if not archivo:
            return

        try:
            self.archivo = Path(archivo)

            audio = AudioSegment.from_mp3(str(self.archivo))

            self.duracion_audio = len(audio) / 1000

            minutos = int(self.duracion_audio // 60)
            segundos = int(self.duracion_audio % 60)

            self.label_archivo.config(
                text=f"Archivo: {self.archivo.name}"
            )

            self.label_duracion.config(
                text=f"Duración: {minutos}:{segundos:02d} "
                     f"({self.duracion_audio:.2f} segundos)"
            )

            self.carpeta_salida = self.archivo.parent

            self.actualizar_cantidad()

        except Exception as e:
            self.archivo = None
            self.duracion_audio = None

            messagebox.showerror(
                "Error",
                f"No se pudo cargar el audio.\n\n{e}"
            )

    def seleccionar_carpeta(self):

        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta de destino"
        )

        if carpeta:
            self.carpeta_salida = Path(carpeta)

            self.label_carpeta.config(
                text=f"Destino: {carpeta}"
            )

    def obtener_parametros(self):

        duracion = float(self.entrada_duracion.get())
        distancia = float(self.entrada_distancia.get())
        inicio = float(self.entrada_inicio.get())

        if duracion <= 0 or distancia <= 0 or inicio < 0:
            raise ValueError(
                "La duración y distancia deben ser mayores a cero. "
                "El segundo inicial no puede ser negativo."
            )

        return duracion, distancia, inicio

    def actualizar_solapamiento(self, event=None):

        try:
            duracion = float(self.entrada_duracion.get())
            distancia = float(self.entrada_distancia.get())

            if duracion <= 0 or distancia <= 0:
                raise ValueError

            solapamiento = max(0, duracion - distancia)

            self.label_solapamiento.config(
                text=f"Solapamiento: {solapamiento:g} segundos"
            )

            self.actualizar_cantidad()

        except ValueError:

            self.label_solapamiento.config(
                text="Configuración pendiente..."
            )

            self.label_cantidad.config(
                text="Clips que se generarán: --"
            )

    def actualizar_cantidad(self):

        if self.duracion_audio is None:
            return

        try:
            duracion, distancia, inicio = self.obtener_parametros()

            duracion_ms = int(duracion * 1000)
            distancia_ms = int(distancia * 1000)
            inicio_ms = int(inicio * 1000)
            audio_ms = int(self.duracion_audio * 1000)

            restante = audio_ms - inicio_ms

            if restante < duracion_ms:
                cantidad = 0
            else:
                cantidad = (
                    (restante - duracion_ms) // distancia_ms
                ) + 1

            self.label_cantidad.config(
                text=f"Clips que se generarán: {cantidad}"
            )

        except ValueError:
            self.label_cantidad.config(
                text="Clips que se generarán: --"
            )


    def dividir_audio(self):

        if not self.archivo:
            messagebox.showwarning(
                "Atención",
                "Primero selecciona un archivo MP3."
            )
            return

        try:
            duracion, distancia, segundo_inicio = (
                self.obtener_parametros()
            )

        except ValueError as e:
            messagebox.showerror("Configuración inválida", str(e))
            return

        try:
            audio = AudioSegment.from_mp3(str(self.archivo))

            duracion_ms = int(duracion * 1000)
            distancia_ms = int(distancia * 1000)
            inicio_ms = int(segundo_inicio * 1000)

            audio_ms = len(audio)

            if inicio_ms >= audio_ms:
                messagebox.showerror(
                    "Error",
                    "El segundo inicial supera la duración del audio."
                )
                return

            restante = audio_ms - inicio_ms

            cantidad = (
                (restante - duracion_ms) // distancia_ms
            ) + 1 if restante >= duracion_ms else 0

            if cantidad == 0:
                messagebox.showwarning(
                    "Atención",
                    "No hay suficiente audio para generar "
                    "un segmento completo."
                )
                return

            # Carpeta de destino
            if self.carpeta_salida is None:
                self.carpeta_salida = self.archivo.parent

            self.carpeta_salida.mkdir(parents=True, exist_ok=True)

            # Nombre base de la canción
            nombre_base = self.archivo.stem

            # Generar clips directamente en la carpeta seleccionada
            for i in range(cantidad):

                inicio = inicio_ms + i * distancia_ms
                final = inicio + duracion_ms

                segmento = audio[inicio:final]

                nombre = f"{nombre_base}_parte{i + 1:03d}.mp3"

                ruta_salida = self.carpeta_salida / nombre

                segmento.export(
                    str(ruta_salida),
                    format="mp3",
                    bitrate="192k"
                )

            messagebox.showinfo(
                "Proceso completado",
                f"Audio dividido correctamente.\n\n"
                f"Clips generados: {cantidad}\n"
                f"Duración por clip: {duracion:g} segundos\n"
                f"Distancia entre clips: {distancia:g} segundos\n"
                f"Solapamiento: {max(0, duracion - distancia):g} segundos\n\n"
                f"Ubicación:\n{self.carpeta_salida}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error al procesar el audio",
                str(e)
            )







if __name__ == "__main__":

    ventana = tk.Tk()

    aplicacion = DivisorAudio(ventana)

    ventana.mainloop()
