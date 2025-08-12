# -*- coding: utf-8 -*-
"""
Frontend (CustomTkinter) para Árbol Genealógico
- Usa el backend en genealogia_core.py
- Estilo minimalista con paleta y gradiente

Ejecutar:
    python genealogia_ui.py

Requiere:
    pip install customtkinter
"""
from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Optional, List, Tuple
from datetime import date

from genealogia_core import (
    Persona, Familia, ArbolGenealogico,
    PROVINCIAS_CR, ESTADOS_CIVILES, GENEROS, AFINIDADES,
    hoy
)

# ------------------------------- Paleta y utilidades UI -------------------------------
PALETTE = {
    "bg_dark": "#172033",   # fondo profundo (sidebar)
    "bg": "#12273b",        # fondo principal
    "panel": "#16324a",     # paneles elevación 1
    "card": "#1b3e58",      # tarjetas/áreas de contenido
    "stroke": "#0e2535",    # bordes sutiles
    "accent": "#01c38e",    # botones, énfasis
    "text": "#ffffff"        # texto
}

class GradientCanvas(tk.Canvas):
    """Canvas con gradiente vertical usando únicamente stdlib."""
    def __init__(self, master, start=PALETTE["bg"], end=PALETTE["bg_dark"], **kw):
        super().__init__(master, highlightthickness=0, bd=0, **kw)
        self.start, self.end = start, end
        self.bind("<Configure>", self._draw)

    def _hex_to_rgb(self, hx):
        hx = hx.lstrip('#')
        return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

    def _interp(self, c1, c2, t):
        return tuple(int(c1[i] + (c2[i]-c1[i]) * t) for i in range(3))

    def _rgb_to_hex(self, rgb):
        return "#%02x%02x%02x" % rgb

    def _draw(self, _evt=None):
        self.delete("grad")
        w, h = self.winfo_width(), self.winfo_height()
        c1, c2 = self._hex_to_rgb(self.start), self._hex_to_rgb(self.end)
        steps = max(2, h)
        for i in range(steps):
            t = i / (steps-1)
            color = self._rgb_to_hex(self._interp(c1, c2, t))
            self.create_line(0, i, w, i, fill=color, tags=("grad",))

# ---- Helpers de estilo para widgets ----
PLACEHOLDER = "#9fb3c8"

def entry(parent, **kw):
    # Mezcla valores por defecto con los provistos en la llamada
    defaults = dict(
        fg_color=PALETTE["card"],
        border_color=PALETTE["stroke"],
        text_color=PALETTE["text"],
        placeholder_text_color=PLACEHOLDER,
    )
    defaults.update(kw)
    return ctk.CTkEntry(parent, **defaults)


def omenu(parent, **kw):
    defaults = dict(
        fg_color=PALETTE["panel"],
        button_color=PALETTE["card"],
        button_hover_color="#234b6a",
        dropdown_fg_color=PALETTE["card"],
        dropdown_hover_color="#21455f",
        text_color=PALETTE["text"],
    )
    defaults.update(kw)
    return ctk.CTkOptionMenu(parent, **defaults)

# ------------------------------- UI (CustomTkinter) -------------------------------
class App(ctk.CTk):
    REFRESH_MS = 1000           # 1s
    EVENTO_CADA = 10            # 10s

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("Árbol Genealógico")
        self.geometry("1100x680")
        self.minsize(980, 620)

        # Fondo con gradiente
        self.bg = GradientCanvas(self, start=PALETTE["bg"], end=PALETTE["bg_dark"]) # azul → navy elegante
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)

        # Modelo
        self.modelo = ArbolGenealogico()

        # Estado
        self.familia_activa: Optional[str] = None
        self.segundos = 0

        # Layout minimalista: sidebar + main
        # Layout minimalista: sidebar + main (grid)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=PALETTE["bg_dark"], border_width=0) 
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.main = ctk.CTkFrame(self, fg_color=PALETTE["bg"], border_width=0) 
        self.main.grid(row=0, column=1, sticky="nsew")

        # Traer al frente sobre el gradiente
        self.sidebar.lift()
        self.main.lift()

        # Sidebar content
        self._build_sidebar()

        # Main views (stack)
        self.frames: Dict[str, tk.Frame] = {}
        self._build_views()

        # Tick
        self.after(self.REFRESH_MS, self._tick)

    # ---------------- Sidebar ----------------
    def _build_sidebar(self):
        title = ctk.CTkLabel(self.sidebar, text="Árbol\nGenealógico", justify="left", font=("Segoe UI", 20, "bold"), text_color=PALETTE["text"])
        title.pack(padx=20, pady=(20, 10), anchor="w")

        self.lbl_familia = ctk.CTkLabel(self.sidebar, text="(sin familia)", font=("Segoe UI", 12), text_color=PALETTE["text"])
        self.lbl_familia.pack(padx=20, pady=(0, 20), anchor="w")

        def add_btn(text, cmd):
            b = ctk.CTkButton(self.sidebar, text=text, command=cmd, corner_radius=18,
                               fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220")
            b.pack(fill="x", padx=16, pady=6)
            return b

        add_btn("Familias", lambda: self._show("familias"))
        add_btn("Personas", lambda: self._show("personas"))
        add_btn("Relaciones", lambda: self._show("relaciones"))
        add_btn("Árbol", lambda: self._show("arbol"))
        add_btn("Búsquedas", lambda: self._show("busquedas"))
        add_btn("Historial", lambda: self._show("historial"))

        self.lbl_tiempo = ctk.CTkLabel(self.sidebar, text="Tiempo: 0s", font=("Segoe UI", 11), text_color=PALETTE["text"])
        self.lbl_tiempo.pack(padx=16, pady=(16, 6), anchor="w")

        self.lbl_fecha = ctk.CTkLabel(self.sidebar, text=f"Fecha sim.: {hoy().isoformat()}", font=("Segoe UI", 11), text_color=PALETTE["text"])
        self.lbl_fecha.pack(padx=16, pady=(0, 16), anchor="w")

    # ---------------- Views ----------------
    def _build_views(self):
        self.frames["familias"] = self._view_familias(self.main)
        self.frames["personas"] = self._view_personas(self.main)
        self.frames["relaciones"] = self._view_relaciones(self.main)
        self.frames["arbol"] = self._view_arbol(self.main)
        self.frames["busquedas"] = self._view_busquedas(self.main)
        self.frames["historial"] = self._view_historial(self.main)
        self._show("familias")

    def _clear_main(self):
        for f in self.main.winfo_children():
            f.pack_forget()

    def _show(self, key: str):
        self._clear_main()
        f = self.frames[key]
        f.pack(fill="both", expand=True)
        if key == "arbol":
            self._redibujar_arbol()
        elif key == "historial":
            self._refrescar_historial()

    # ---------------- View: Familias ----------------
    def _view_familias(self, parent) -> tk.Frame:
        frame = ctk.CTkFrame(parent, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        top = ctk.CTkFrame(frame, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        top.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(top, text="Gestión de familias", font=("Segoe UI", 18, "bold"), text_color=PALETTE["text"]).pack(anchor="w")

        form = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        form.pack(fill="x", padx=16, pady=(0, 16))

        self.id_fam_var = tk.StringVar()
        self.nom_fam_var = tk.StringVar()
        entry(form, placeholder_text="ID familia", textvariable=self.id_fam_var).pack(side="left", padx=6)
        entry(form, placeholder_text="Nombre familia", textvariable=self.nom_fam_var, width=240).pack(side="left", padx=6)
        ctk.CTkButton(form, text="Crear", command=self._crear_familia, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(side="left", padx=6)

        listf = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        listf.pack(fill="both", expand=True, padx=16, pady=16)
        self.lst_familias = tk.Listbox(listf, bg=PALETTE["card"], fg=PALETTE["text"], highlightthickness=0, selectbackground=PALETTE["accent"], selectforeground="#0b1220", relief="flat")
        self.lst_familias.pack(side="left", fill="both", expand=True)
        sb = ctk.CTkScrollbar(listf, command=self.lst_familias.yview)
        sb.pack(side="right", fill="y")
        self.lst_familias.config(yscrollcommand=sb.set)
        self.lst_familias.bind("<<ListboxSelect>>", self._seleccionar_familia)

        return frame

    def _crear_familia(self):
        idf = self.id_fam_var.get().strip()
        nom = self.nom_fam_var.get().strip()
        if not idf or not nom:
            messagebox.showwarning("Validación", "Ingrese ID y nombre")
            return
        try:
            self.modelo.crear_familia(idf, nom)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self._refrescar_lista_familias()
        self.id_fam_var.set("")
        self.nom_fam_var.set("")

    def _refrescar_lista_familias(self):
        self.lst_familias.delete(0, tk.END)
        for fam in self.modelo.familias.values():
            self.lst_familias.insert(tk.END, f"{fam.id_familia} • {fam.nombre} ({len(fam.miembros)} miembros)")

    def _seleccionar_familia(self, _evt=None):
        idx = self.lst_familias.curselection()
        if not idx:
            return
        seleccionado = self.lst_familias.get(idx[0])
        idf = seleccionado.split(" • ")[0]
        self.familia_activa = idf
        self.lbl_familia.configure(text=f"Familia: {idf}")
        self._refrescar_personas()

    # ---------------- View: Personas ----------------
    def _view_personas(self, parent) -> tk.Frame:
        frame = ctk.CTkFrame(parent, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)

        top = ctk.CTkFrame(frame, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        top.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(top, text="Integrantes de familia", font=("Segoe UI", 18, "bold"), text_color=PALETTE["text"]).pack(anchor="w")

        form = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        form.pack(fill="x", padx=16, pady=(0, 10))

        self.ced_var = tk.StringVar()
        self.nom_var = tk.StringVar()
        self.fnac_var = tk.StringVar(value=hoy().isoformat())
        self.gen_var = tk.StringVar(value=GENEROS[0])
        self.prov_var = tk.StringVar(value=PROVINCIAS_CR[0])
        self.eciv_var = tk.StringVar(value=ESTADOS_CIVILES[0])
        self.af1_var = tk.StringVar(value=AFINIDADES[0])
        self.af2_var = tk.StringVar(value=AFINIDADES[1])

        row1 = ctk.CTkFrame(form)
        row1.pack(fill="x", pady=4)
        entry(row1, placeholder_text="Cédula", textvariable=self.ced_var, width=120).pack(side="left", padx=4)
        entry(row1, placeholder_text="Nombre", textvariable=self.nom_var, width=200).pack(side="left", padx=4)
        entry(row1, placeholder_text="YYYY-MM-DD", textvariable=self.fnac_var, width=120).pack(side="left", padx=4)
        omenu(row1, values=GENEROS, variable=self.gen_var, width=140).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(form)
        row2.pack(fill="x", pady=4)
        omenu(row2, values=PROVINCIAS_CR, variable=self.prov_var, width=160).pack(side="left", padx=4)
        omenu(row2, values=ESTADOS_CIVILES, variable=self.eciv_var, width=160).pack(side="left", padx=4)
        omenu(row2, values=AFINIDADES, variable=self.af1_var, width=160).pack(side="left", padx=4)
        omenu(row2, values=AFINIDADES, variable=self.af2_var, width=160).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Agregar persona", command=self._agregar_persona, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(side="left", padx=8)

        mid = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        mid.pack(fill="both", expand=True, padx=16, pady=16)
        self.lst_personas = tk.Listbox(mid, bg=PALETTE["card"], fg=PALETTE["text"], highlightthickness=0, selectbackground=PALETTE["accent"], selectforeground="#0b1220", relief="flat")
        self.lst_personas.pack(side="left", fill="both", expand=True)
        sb = ctk.CTkScrollbar(mid, command=self.lst_personas.yview)
        sb.pack(side="right", fill="y")
        self.lst_personas.config(yscrollcommand=sb.set)

        return frame

    def _agregar_persona(self):
        if not self.familia_activa:
            messagebox.showwarning("Familia", "Seleccione/cree una familia primero")
            return
        try:
            fnac = date.fromisoformat(self.fnac_var.get())
        except Exception:
            messagebox.showerror("Fecha", "Formato de fecha inválido. Use YYYY-MM-DD")
            return
        p = Persona(
            cedula=self.ced_var.get().strip(),
            nombre=self.nom_var.get().strip(),
            fecha_nacimiento=fnac,
            genero=self.gen_var.get(),
            provincia=self.prov_var.get(),
            estado_civil=self.eciv_var.get(),
            afinidades={self.af1_var.get(), self.af2_var.get()},
        )
        if not p.cedula or not p.nombre:
            messagebox.showwarning("Validación", "Cédula y nombre son obligatorios")
            return
        try:
            self.modelo.agregar_persona(self.familia_activa, p)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self._refrescar_personas()
        self.ced_var.set("")
        self.nom_var.set("")

    def _refrescar_personas(self):
        if not self.familia_activa:
            return
        fam = self.modelo.get_familia(self.familia_activa)
        if not fam:
            return
        self.lst_personas.delete(0, tk.END)
        for p in sorted(fam.todas_personas(), key=lambda x: x.nombre):
            vivo = "🟢" if p.vivo else "⚫"
            self.lst_personas.insert(tk.END, f"{vivo} {p.nombre} ({p.cedula}) • {p.edad(self.modelo.fecha_simulada)} años • {p.estado_civil}")

    # ---------------- View: Relaciones ----------------
    def _view_relaciones(self, parent) -> tk.Frame:
        frame = ctk.CTkFrame(parent, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        ctk.CTkLabel(frame, text="Relaciones", font=("Segoe UI", 18, "bold"), text_color=PALETTE["text"]).pack(anchor="w", padx=16, pady=16)

        # Uniones
        sec_union = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        sec_union.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(sec_union, text="Unir pareja / Matrimonio").pack(side="left")
        self.ced_a_var = tk.StringVar()
        self.ced_b_var = tk.StringVar()
        entry(sec_union, placeholder_text="Cédula A", textvariable=self.ced_a_var, width=120).pack(side="left", padx=6)
        entry(sec_union, placeholder_text="Cédula B", textvariable=self.ced_b_var, width=120).pack(side="left", padx=6)
        ctk.CTkButton(sec_union, text="Unir pareja", command=self._unir_pareja, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(side="left", padx=6)
        ctk.CTkButton(sec_union, text="Matrimonio", command=self._matrimonio, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(side="left", padx=6)

        # Padre-Hijo
        sec_ph = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        sec_ph.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(sec_ph, text="Registrar parentesco padre/madre ↔ hijo(a)").pack(side="left")
        self.ced_padre_var = tk.StringVar()
        self.ced_hijo_var = tk.StringVar()
        entry(sec_ph, placeholder_text="Cédula padre/madre", textvariable=self.ced_padre_var, width=160).pack(side="left", padx=6)
        entry(sec_ph, placeholder_text="Cédula hijo(a)", textvariable=self.ced_hijo_var, width=140).pack(side="left", padx=6)
        ctk.CTkButton(sec_ph, text="Vincular", command=self._padre_hijo, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(side="left", padx=6)

        # Nacimiento de pareja
        sec_nac = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        sec_nac.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(sec_nac, text="Hijo(a) de la pareja").pack(side="left")
        self.ced_pa_var = tk.StringVar()
        self.ced_pb_var = tk.StringVar()
        entry(sec_nac, placeholder_text="Cédula A", textvariable=self.ced_pa_var, width=120).pack(side="left", padx=6)
        entry(sec_nac, placeholder_text="Cédula B", textvariable=self.ced_pb_var, width=120).pack(side="left", padx=6)
        ctk.CTkButton(sec_nac, text="Registrar nacimiento", command=self._nacimiento_pareja, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(side="left", padx=6)

        return frame

    def _unir_pareja(self):
        if not self.familia_activa:
            return
        ok = self.modelo.unir_pareja(self.familia_activa, self.ced_a_var.get(), self.ced_b_var.get())
        if not ok:
            messagebox.showinfo("Unión", "No fue posible unir (verifique compatibilidad y datos)")
        else:
            messagebox.showinfo("Unión", "Pareja unida")
        self._refrescar_personas()

    def _matrimonio(self):
        if not self.familia_activa:
            return
        ok = self.modelo.registrar_matrimonio(self.familia_activa, self.ced_a_var.get(), self.ced_b_var.get())
        if not ok:
            messagebox.showinfo("Matrimonio", "No fue posible registrar el matrimonio")
        else:
            messagebox.showinfo("Matrimonio", "Matrimonio registrado")
        self._refrescar_personas()

    def _padre_hijo(self):
        if not self.familia_activa:
            return
        ok = self.modelo.registrar_padre_hijo(self.familia_activa, self.ced_padre_var.get(), self.ced_hijo_var.get())
        if not ok:
            messagebox.showinfo("Parentesco", "No fue posible vincular padre-hijo")
        else:
            messagebox.showinfo("Parentesco", "Vinculado")

    def _nacimiento_pareja(self):
        if not self.familia_activa:
            return
        p = self.modelo.registrar_nacimiento_de_pareja(self.familia_activa, self.ced_pa_var.get(), self.ced_pb_var.get())
        if not p:
            messagebox.showinfo("Nacimiento", "No fue posible registrar el nacimiento")
        else:
            messagebox.showinfo("Nacimiento", f"Nació {p.nombre} ({p.cedula})")
        self._refrescar_personas()

    # ---------------- View: Árbol (Canvas) ----------------
    def _view_arbol(self, parent) -> tk.Frame:
        frame = ctk.CTkFrame(parent, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        ctk.CTkLabel(frame, text="Árbol genealógico", font=("Segoe UI", 18, "bold"), text_color=PALETTE["text"]).pack(anchor="w", padx=16, pady=16)
        self.canvas_arbol = tk.Canvas(frame, bg=PALETTE["card"], highlightthickness=0)
        self.canvas_arbol.pack(fill="both", expand=True, padx=16, pady=16)
        return frame

    def _layout_generacional(self, fam: Familia) -> Dict[str, int]:
        """Asigna nivel (generación) por BFS desde ancestros sin padres."""
        nivel: Dict[str, int] = {}
        # raíces = quienes no tienen padres o padres fuera de familia
        raices = [p for p in fam.todas_personas() if not p.padres]
        queue: List[Tuple[str, int]] = [(p.cedula, 0) for p in raices]
        for p in fam.todas_personas():
            if p.padres and all((fam.obtener(c) is None) for c in p.padres):
                queue.append((p.cedula, 0))
        seen = set()
        while queue:
            ced, niv = queue.pop(0)
            if ced in seen:
                continue
            seen.add(ced)
            nivel[ced] = min(niv, nivel.get(ced, niv))
            pers = fam.obtener(ced)
            if pers:
                for h in pers.hijos:
                    queue.append((h, niv + 1))
        return nivel

    def _redibujar_arbol(self):
        self.canvas_arbol.delete("all")
        if not self.familia_activa:
            return
        fam = self.modelo.get_familia(self.familia_activa)
        if not fam or not fam.miembros:
            return
        niveles = self._layout_generacional(fam)
        # agrupar por nivel
        por_nivel: Dict[int, List[Persona]] = {}
        for ced, niv in niveles.items():
            p = fam.obtener(ced)
            if p:
                por_nivel.setdefault(niv, []).append(p)
        # ordenar por nombre
        for niv in por_nivel:
            por_nivel[niv].sort(key=lambda x: x.nombre)

        w = self.canvas_arbol.winfo_width() or 800
        box_w, box_h = 150, 40
        vgap = 80
        colors = {True: "#01c38e", False: "#2b3a4d"}

        pos: Dict[str, Tuple[int, int]] = {}
        niveles_ordenados = sorted(por_nivel.keys())
        for i, niv in enumerate(niveles_ordenados):
            fila = por_nivel[niv]
            n = len(fila)
            if n == 0:
                continue
            total_w = n * box_w + (n - 1) * 20
            x0 = (w - total_w) // 2
            y = 40 + i * (box_h + vgap)
            for j, p in enumerate(fila):
                x = x0 + j * (box_w + 20)
                pos[p.cedula] = (x, y)
                # caja
                self.canvas_arbol.create_rectangle(x, y, x + box_w, y + box_h, fill=colors[p.vivo], outline=PALETTE["stroke"], width=1)
                self.canvas_arbol.create_text(x + 8, y + 8, anchor="nw", fill=PALETTE["text"], font=("Segoe UI", 11, "bold"), text=p.nombre)
                self.canvas_arbol.create_text(x + 8, y + 24, anchor="nw", fill="#c9d4df", font=("Segoe UI", 9), text=f"{p.edad(self.modelo.fecha_simulada)} años")
        # líneas padres → hijos
        for p in fam.todas_personas():
            for h in p.hijos:
                if p.cedula in pos and h in pos:
                    x1, y1 = pos[p.cedula]
                    x2, y2 = pos[h]
                    self.canvas_arbol.create_line(x1 + box_w // 2, y1 + box_h, x2 + box_w // 2, y2, fill="#7a8ba0")

    # ---------------- View: Búsquedas ----------------
    def _view_busquedas(self, parent) -> tk.Frame:
        frame = ctk.CTkFrame(parent, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        ctk.CTkLabel(frame, text="Consultas", font=("Segoe UI", 18, "bold"), text_color=PALETTE["text"]).pack(anchor="w", padx=16, pady=16)

        def row(label):
            rf = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
            rf.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(rf, text=label, width=260, anchor="w").pack(side="left")
            e1, e2 = tk.StringVar(), tk.StringVar()
            c1 = entry(rf, placeholder_text="Cédula A", textvariable=e1, width=160)
            c2 = entry(rf, placeholder_text="Cédula B", textvariable=e2, width=160)
            c1.pack(side="left", padx=4)
            c2.pack(side="left", padx=4)
            out = ctk.CTkLabel(rf, text="", anchor="w")
            out.pack(side="left", padx=8)
            return e1, e2, out

        # 1 relación A-B
        self.q1_a, self.q1_b, self.q1_out = row("1) Relación entre A y B")
        ctk.CTkButton(frame, text="Consultar 1", command=self._q1, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(anchor="w", padx=16)

        # 2 primos de X
        rf2 = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        rf2.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf2, text="2) Primos de primer grado de X", width=260, anchor="w").pack(side="left")
        self.q2_x = tk.StringVar()
        entry(rf2, placeholder_text="Cédula X", textvariable=self.q2_x, width=160).pack(side="left", padx=4)
        self.q2_out = ctk.CTkLabel(rf2, text="", anchor="w")
        self.q2_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 2", command=self._q2, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(anchor="w", padx=16)

        # 3 antepasados maternos
        rf3 = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        rf3.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf3, text="3) Antepasados maternos de X", width=260, anchor="w").pack(side="left")
        self.q3_x = tk.StringVar()
        entry(rf3, placeholder_text="Cédula X", textvariable=self.q3_x, width=160).pack(side="left", padx=4)
        self.q3_out = ctk.CTkLabel(rf3, text="", anchor="w")
        self.q3_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 3", command=self._q3, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(anchor="w", padx=16)

        # 4 descendientes vivos
        rf4 = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        rf4.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf4, text="4) Descendientes vivos de X", width=260, anchor="w").pack(side="left")
        self.q4_x = tk.StringVar()
        entry(rf4, placeholder_text="Cédula X", textvariable=self.q4_x, width=160).pack(side="left", padx=4)
        self.q4_out = ctk.CTkLabel(rf4, text="", anchor="w")
        self.q4_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 4", command=self._q4, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(anchor="w", padx=16)

        # 5 nacidos últimos 10 años
        rf5 = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        rf5.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf5, text="5) ¿Cuántos nacieron en los últimos 10 años?", width=260, anchor="w").pack(side="left")
        self.q5_out = ctk.CTkLabel(rf5, text="", anchor="w")
        self.q5_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 5", command=self._q5, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(anchor="w", padx=16)

        # 6 parejas con 2+ hijos
        rf6 = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        rf6.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf6, text="6) Parejas con 2+ hijos", width=260, anchor="w").pack(side="left")
        self.q6_out = ctk.CTkLabel(rf6, text="", anchor="w")
        self.q6_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 6", command=self._q6, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(anchor="w", padx=16)

        # 7 fallecidos < 50
        rf7 = ctk.CTkFrame(frame, fg_color=PALETTE["card"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        rf7.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf7, text="7) Fallecidos antes de 50 años", width=260, anchor="w").pack(side="left")
        self.q7_out = ctk.CTkLabel(rf7, text="", anchor="w")
        self.q7_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 7", command=self._q7, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(anchor="w", padx=16)

        return frame

    def _q1(self):
        fam = self.modelo.get_familia(self.familia_activa) if self.familia_activa else None
        if not fam:
            return
        self.q1_out.configure(text=self.modelo.relacion_entre(fam, self.q1_a.get(), self.q1_b.get()))

    def _q2(self):
        fam = self.modelo.get_familia(self.familia_activa) if self.familia_activa else None
        if not fam:
            return
        nombres = ", ".join(p.nombre for p in self.modelo.primos_primer_grado(fam, self.q2_x.get()))
        self.q2_out.configure(text=nombres or "(ninguno)")

    def _q3(self):
        fam = self.modelo.get_familia(self.familia_activa) if self.familia_activa else None
        if not fam:
            return
        nombres = ", ".join(p.nombre for p in self.modelo.antepasados_maternos(fam, self.q3_x.get()))
        self.q3_out.configure(text=nombres or "(ninguno)")

    def _q4(self):
        fam = self.modelo.get_familia(self.familia_activa) if self.familia_activa else None
        if not fam:
            return
        nombres = ", ".join(p.nombre for p in self.modelo.descendientes_vivos(fam, self.q4_x.get()))
        self.q4_out.configure(text=nombres or "(ninguno)")

    def _q5(self):
        fam = self.modelo.get_familia(self.familia_activa) if self.familia_activa else None
        if not fam:
            return
        n = len(self.modelo.nacidos_ultimos_10_anios(fam))
        self.q5_out.configure(text=f"{n}")

    def _q6(self):
        fam = self.modelo.get_familia(self.familia_activa) if self.familia_activa else None
        if not fam:
            return
        pares = self.modelo.parejas_con_mas_de_dos_hijos(fam)
        txt = ", ".join(f"{a.nombre} & {b.nombre}" for a, b in pares) or "(ninguna)"
        self.q6_out.configure(text=txt)

    def _q7(self):
        fam = self.modelo.get_familia(self.familia_activa) if self.familia_activa else None
        if not fam:
            return
        txt = ", ".join(p.nombre for p in self.modelo.fallecidos_antes_de_50(fam)) or "(ninguno)"
        self.q7_out.configure(text=txt)

    # ---------------- View: Historial ----------------
    def _view_historial(self, parent) -> tk.Frame:
        frame = ctk.CTkFrame(parent, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        ctk.CTkLabel(frame, text="Historial y línea del tiempo", font=("Segoe UI", 18, "bold"), text_color=PALETTE["text"]).pack(anchor="w", padx=16, pady=16)

        top = ctk.CTkFrame(frame, fg_color=PALETTE["panel"], corner_radius=16, border_color=PALETTE["stroke"], border_width=1)
        top.pack(fill="x", padx=16, pady=6)
        self.hist_ced_var = tk.StringVar()
        entry(top, placeholder_text="Cédula", textvariable=self.hist_ced_var, width=180).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Ver historial", command=self._refrescar_historial, fg_color=PALETTE["accent"], hover_color="#00a67a", text_color="#0b1220").pack(side="left", padx=6)

        self.txt_hist = tk.Text(frame, height=14, bg=PALETTE["card"], fg=PALETTE["text"], insertbackground=PALETTE["text"], relief="flat")
        self.txt_hist.pack(fill="both", expand=True, padx=16, pady=10)

        # Timeline visual simple
        self.canvas_timeline = tk.Canvas(frame, height=120, bg=PALETTE["card"], highlightthickness=0)
        self.canvas_timeline.pack(fill="x", padx=16, pady=(0, 16))

        return frame

    def _refrescar_historial(self):
        self.txt_hist.delete("1.0", tk.END)
        self.canvas_timeline.delete("all")
        if not self.familia_activa:
            return
        fam = self.modelo.get_familia(self.familia_activa)
        if not fam:
            return
        p = fam.obtener(self.hist_ced_var.get().strip()) if self.hist_ced_var.get().strip() else None
        if not p:
            self.txt_hist.insert(tk.END, "Ingrese cédula para ver historial\n")
            return
        for anio, ev in sorted(p.historial):
            self.txt_hist.insert(tk.END, f"{anio}: {ev}\n")
        # Timeline
        if p.historial:
            years = [a for a, _ in p.historial]
            y_min, y_max = min(years), max(years)
            w = self.canvas_timeline.winfo_width() or 800
            margin = 40
            self.canvas_timeline.create_line(margin, 60, w - margin, 60, fill="#7a8ba0")
            span = max(1, y_max - y_min)
            for anio, ev in sorted(p.historial):
                x = margin + int((w - 2 * margin) * (anio - y_min) / span)
                self.canvas_timeline.create_oval(x - 4, 56, x + 4, 64, fill=PALETTE["accent"], outline="")
                self.canvas_timeline.create_text(x, 75, text=str(anio), fill="#c9d4df", font=("Segoe UI", 9))
                self.canvas_timeline.create_text(x, 95, text=ev, fill=PALETTE["text"], font=("Segoe UI", 9))

    # ---------------- Reloj / Motor de eventos ----------------
    def _tick(self):
        self.segundos += 1
        self.lbl_tiempo.configure(text=f"Tiempo: {self.segundos}s")
        self.lbl_fecha.configure(text=f"Fecha sim.: {self.modelo.fecha_simulada.isoformat()}")
        if self.familia_activa and self.segundos % self.EVENTO_CADA == 0:
            # Ejecutar eventos
            self.modelo.evento_cada_10s(self.familia_activa)
            # Refrescar vistas posibles
            self._refrescar_personas()
            if self.frames.get("arbol") and str(self.frames["arbol"].winfo_ismapped()):
                self._redibujar_arbol()
            if self.frames.get("historial") and str(self.frames["historial"].winfo_ismapped()):
                self._refrescar_historial()
        self.after(self.REFRESH_MS, self._tick)


if __name__ == "__main__":
    app = App()
    # Semilla de ejemplo opcional (se puede borrar)
    try:
        app.modelo.crear_familia("F1", "Familia Demo")
        app.familia_activa = "F1"
        app.lbl_familia.configure(text="Familia: F1")
        base_date = date(1985, 5, 10)
        demo = [
            Persona("101", "Ana", base_date, "Femenino", "San José", afinidades={"Arte", "Música"}),
            Persona("102", "Luis", date(1982, 3, 2), "Masculino", "Alajuela", afinidades={"Deporte", "Viajes"}),
            Persona("201", "Marta", date(1960, 7, 1), "Femenino", "Cartago", afinidades={"Lectura", "Gastronomía"}),
            Persona("202", "Carlos", date(1958, 1, 20), "Masculino", "Cartago", afinidades={"Ciencia", "Lectura"}),
        ]
        for p in demo:
            app.modelo.agregar_persona("F1", p)
        # padres de Ana = Marta & Carlos
        app.modelo.registrar_padre_hijo("F1", "201", "101")
        app.modelo.registrar_padre_hijo("F1", "202", "101")
        # unir Ana & Luis
        app.modelo.unir_pareja("F1", "101", "102")
    except Exception:
        pass

    app._refrescar_lista_familias()
    app._refrescar_personas()
    app.mainloop()
