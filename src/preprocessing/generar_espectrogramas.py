import os
import queue
import shutil
import threading
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog, messagebox, ttk

import numpy as np
import librosa
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


SR = 22050          
DURACION = 30       
N_FFT = 1024        
HOP = 512           
N_MELS = 128        
TOP_DB = 80         
N_FRAMES = 1 + (SR * DURACION) // HOP   
EXTENSIONES = (".mp3", ".wav", ".flac", ".ogg")
N_TEST = 2          



def audio_a_espectrograma(ruta):
    
    y, _ = librosa.load(ruta, sr=SR, mono=True, duration=DURACION)
    y = librosa.util.fix_length(y, size=SR * DURACION)       
    mel = librosa.feature.melspectrogram(
        y=y, sr=SR, n_fft=N_FFT, hop_length=HOP, n_mels=N_MELS, power=2.0)
    mel_db = librosa.power_to_db(mel, ref=np.max, top_db=TOP_DB)   
    x = (mel_db + TOP_DB / 2) / (TOP_DB / 2)                       
    x = np.clip(x, -1, 1).astype(np.float32)
    return x[:, :N_FRAMES]


def nombre_cancion(archivo):
    base = os.path.splitext(archivo)[0]
    return base.rsplit("_parte", 1)[0]


def agrupar_por_cancion(carpeta):
    
    grupos = defaultdict(list)
    for f in sorted(os.listdir(carpeta)):
        if f.lower().endswith(EXTENSIONES):
            grupos[nombre_cancion(f)].append(f)
    return dict(grupos)


def procesar(entrada, salida, grupos, test_set, q):
    
    try:
        total = sum(len(v) for v in grupos.values())
        hecho = 0
        contador = {"train": 0, "test": 0}
        for cancion, lista in grupos.items():
            split = "test" if cancion in test_set else "train"
            destino = os.path.join(salida, split)
            for i, f in enumerate(lista):
                x = audio_a_espectrograma(os.path.join(entrada, f))
                np.save(os.path.join(destino, os.path.splitext(f)[0] + ".npy"), x)
                contador[split] += 1
                hecho += 1
                q.put(("progreso", hecho, total))
                if i == 0:
                    q.put(("preview", x, f"[{split}] {cancion}"))
            q.put(("log", f"[{split}] {cancion}  ({len(lista)} clips)"))
        q.put(("fin", contador))
    except Exception as e:  # noqa: BLE001
        q.put(("error", str(e)))



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generador de espectrogramas - CycleGAN")
        self.geometry("900x640")
        self.entrada = tk.StringVar()
        self.salida = tk.StringVar()
        self.grupos = {}
        self.canciones = []
        self.q = queue.Queue()
        self._crear_widgets()

    def _crear_widgets(self):
        pad = {"padx": 8, "pady": 4}

        # --- Rutas ---
        marco = ttk.LabelFrame(self, text="1. Carpetas")
        marco.pack(fill="x", **pad)
        ttk.Label(marco, text="Clips de audio:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(marco, textvariable=self.entrada, width=70).grid(row=0, column=1, **pad)
        ttk.Button(marco, text="Examinar...", command=self.elegir_entrada).grid(row=0, column=2, **pad)
        ttk.Label(marco, text="Guardar en:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(marco, textvariable=self.salida, width=70).grid(row=1, column=1, **pad)
        ttk.Button(marco, text="Examinar...", command=self.elegir_salida).grid(row=1, column=2, **pad)

        
        medio = ttk.Frame(self)
        medio.pack(fill="both", expand=True, **pad)

        izq = ttk.LabelFrame(medio, text=f"2. Marca {N_TEST} canciones para TEST (Ctrl+clic)")
        izq.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.lista = tk.Listbox(izq, selectmode="multiple", exportselection=False, height=14)
        sb = ttk.Scrollbar(izq, command=self.lista.yview)
        self.lista.config(yscrollcommand=sb.set)
        self.lista.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        sb.pack(side="right", fill="y", pady=4)
        self.lista.bind("<<ListboxSelect>>", self.actualizar_contador)

        der = ttk.LabelFrame(medio, text="Vista previa")
        der.pack(side="right", fill="both", expand=True, padx=(4, 0))
        self.fig = Figure(figsize=(4.2, 3), dpi=90)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("(se mostrará al generar)", fontsize=8)
        self.canvas = FigureCanvasTkAgg(self.fig, master=der)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        
        self.lbl_info = ttk.Label(self, text="Elige la carpeta de clips para empezar.")
        self.lbl_info.pack(anchor="w", **pad)

        self.btn = ttk.Button(self, text="Generar espectrogramas", command=self.generar)
        self.btn.pack(**pad)
        self.barra = ttk.Progressbar(self, mode="determinate")
        self.barra.pack(fill="x", **pad)

        self.log = tk.Text(self, height=8, state="disabled")
        self.log.pack(fill="both", **pad)

    
    def escribir(self, texto):
        self.log.config(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def elegir_entrada(self):
        ruta = filedialog.askdirectory(title="Carpeta con los clips")
        if not ruta:
            return
        self.entrada.set(ruta)
        self.grupos = agrupar_por_cancion(ruta)
        self.canciones = sorted(self.grupos)
        self.lista.delete(0, "end")
        for c in self.canciones:
            self.lista.insert("end", f"{c}   ({len(self.grupos[c])} clips)")
        total = sum(len(v) for v in self.grupos.values())
        self.lbl_info.config(text=f"{total} clips, {len(self.canciones)} canciones detectadas.")
        if not self.canciones:
            messagebox.showwarning("Sin audios", "No se encontraron audios en esa carpeta.")

    def elegir_salida(self):
        ruta = filedialog.askdirectory(title="Carpeta de salida")
        if ruta:
            self.salida.set(ruta)

    def actualizar_contador(self, _evento=None):
        n = len(self.lista.curselection())
        self.lbl_info.config(text=f"Canciones marcadas para test: {n}/{N_TEST}")

    def generar(self):
        entrada, salida = self.entrada.get(), self.salida.get()
        if not self.canciones:
            messagebox.showwarning("Falta información", "Primero elige la carpeta de clips.")
            return
        if not salida:
            messagebox.showwarning("Falta información", "Elige la carpeta de salida.")
            return
        marcadas = self.lista.curselection()
        if len(marcadas) != N_TEST:
            messagebox.showwarning("Test", f"Debes marcar exactamente {N_TEST} canciones para test.")
            return
        test_set = {self.canciones[i] for i in marcadas}

        # Preparar carpetas (evita que un clip quede en train y test a la vez)
        existentes = any(
            os.path.isdir(os.path.join(salida, s)) and os.listdir(os.path.join(salida, s))
            for s in ("train", "test"))
        if existentes:
            if not messagebox.askyesno(
                    "Salida con archivos",
                    "La carpeta de salida ya tiene archivos en train/test.\n"
                    "¿Borrarlos y generar de nuevo?"):
                return
            for s in ("train", "test"):
                shutil.rmtree(os.path.join(salida, s), ignore_errors=True)
        for s in ("train", "test"):
            os.makedirs(os.path.join(salida, s), exist_ok=True)

        self.escribir("Canciones TEST: " + " | ".join(sorted(test_set)))
        self.btn.config(state="disabled")
        self.barra["value"] = 0
        threading.Thread(
            target=procesar, args=(entrada, salida, self.grupos, test_set, self.q),
            daemon=True).start()
        self.after(100, self.revisar_cola)

    def revisar_cola(self):
        seguir = True
        try:
            while True:
                msg = self.q.get_nowait()
                if msg[0] == "progreso":
                    self.barra["maximum"], self.barra["value"] = msg[2], msg[1]
                elif msg[0] == "log":
                    self.escribir(msg[1])
                elif msg[0] == "preview":
                    self.ax.clear()
                    self.ax.imshow(msg[1], origin="lower", aspect="auto",
                                   cmap="magma", vmin=-1, vmax=1)
                    self.ax.set_title(msg[2][:50], fontsize=8)
                    self.ax.set_xlabel("frames", fontsize=7)
                    self.ax.set_ylabel("banda mel", fontsize=7)
                    self.fig.tight_layout()
                    self.canvas.draw_idle()
                elif msg[0] == "fin":
                    c = msg[1]
                    self.escribir(f"\nListo. train: {c['train']} | test: {c['test']}")
                    self.escribir(f"Forma de cada espectrograma: ({N_MELS}, {N_FRAMES})")
                    self.btn.config(state="normal")
                    messagebox.showinfo("Terminado", f"train: {c['train']} | test: {c['test']}")
                    seguir = False
                elif msg[0] == "error":
                    self.escribir("ERROR: " + msg[1])
                    self.btn.config(state="normal")
                    messagebox.showerror("Error", msg[1])
                    seguir = False
        except queue.Empty:
            pass
        if seguir:
            self.after(100, self.revisar_cola)


if __name__ == "__main__":
    App().mainloop()