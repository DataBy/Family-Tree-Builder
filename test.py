# -*- coding: utf-8 -*-
"""
Aplicación minimalista de Árbol Genealógico
Requisitos clave del enunciado:
- POO
- Interfaz gráfica (CustomTkinter)
- Sin archivos, todo en memoria
- Sin librerías de alto nivel (numpy/pandas), solo stdlib
- Gestión de familias, personas, relaciones
- Motor de eventos (cada 10s: cumpleaños / fallecimientos / posibles uniones / nacimientos)
- Efectos colaterales básicos (viudez, tutoría de menores)
- Historial por persona + línea del tiempo visual simple
- Representación gráfica del árbol (canvas simple por generaciones)
- Búsquedas solicitadas

Autor: ChatGPT (plantilla lista para iterar)
"""
from __future__ import annotations
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import date, datetime, timedelta
import random

# ------------------------------- Datos base (listas para menús) -------------------------------
PROVINCIAS_CR = [
    "San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón"
]
ESTADOS_CIVILES = [
    "Soltero(a)", "Casado(a)", "Unión libre", "Viudo(a)", "Divorciado(a)"
]
GENEROS = ["Masculino", "Femenino", "Otro"]

# Para afinidades (mínimo 2), se usan etiquetas simples
AFINIDADES = [
    "Deporte", "Arte", "Ciencia", "Música", "Lectura", "Viajes", "Gastronomía", "Videojuegos"
]

# ------------------------------- Modelo de dominio -------------------------------

def hoy() -> date:
    return date.today()


def anios_entre(fecha: date, ref: Optional[date] = None) -> int:
    if fecha is None:
        return 0
    ref = ref or hoy()
    y = ref.year - fecha.year
    if (ref.month, ref.day) < (fecha.month, fecha.day):
        y -= 1
    return max(0, y)


@dataclass
class Persona:
    cedula: str
    nombre: str
    fecha_nacimiento: date
    genero: str
    provincia: str
    estado_civil: str = "Soltero(a)"
    fecha_fallecimiento: Optional[date] = None

    # Relaciones
    padres: Set[str] = field(default_factory=set)       # cédulas
    hijos: Set[str] = field(default_factory=set)        # cédulas
    parejas: Set[str] = field(default_factory=set)      # cédulas (uniones activas)

    # Afinidades (al menos 2 etiquetas)
    afinidades: Set[str] = field(default_factory=set)

    # Historial (tuplas: (año, evento))
    historial: List[Tuple[int, str]] = field(default_factory=list)

    # Salud emocional (0-100), afecta esperanza de vida de forma simple
    salud_emocional: int = 75

    def edad(self, ref: Optional[date] = None) -> int:
        if self.fecha_fallecimiento:
            return anios_entre(self.fecha_nacimiento, self.fecha_fallecimiento)
        return anios_entre(self.fecha_nacimiento, ref)

    @property
    def vivo(self) -> bool:
        return self.fecha_fallecimiento is None

    def registrar_evento(self, descripcion: str, fecha_ref: Optional[date] = None):
        f = fecha_ref or hoy()
        self.historial.append((f.year, descripcion))

    def marcar_fallecido(self, fecha_def: Optional[date] = None):
        if self.fecha_fallecimiento is None:
            self.fecha_fallecimiento = fecha_def or hoy()
            self.estado_civil = "Viudo(a)" if self.parejas else self.estado_civil
            self.registrar_evento("Fallecimiento")

    def es_compatible_para_union(self, otra: "Persona") -> bool:
        if not self.vivo or not otra.vivo:
            return False
        # Reglas base
        if self.estado_civil in ("Casado(a)", "Unión libre"):
            return False
        if otra.estado_civil in ("Casado(a)", "Unión libre"):
            return False
        if self.edad() < 18 or otra.edad() < 18:
            return False
        if abs(self.edad() - otra.edad()) > 15:
            return False
        # Índice de compatibilidad simple: afinidades compartidas y balance genético naive
        afin_comun = len(self.afinidades.intersection(otra.afinidades))
        afin_total = len(self.afinidades.union(otra.afinidades)) or 1
        score_afinidad = int(100 * (afin_comun / afin_total))  # 0..100
        score_emocional = (self.salud_emocional + otra.salud_emocional) // 2
        # "Compatibilidad genética" naive: penalizar si comparten ambos padres (evitar consanguinidad directa)
        comp_genetica = 100
        if self.padres and self.padres == otra.padres:
            comp_genetica = 20  # muy bajo si comparten ambos padres
        # Índice total ponderado
        indice = int(0.6 * score_afinidad + 0.2 * score_emocional + 0.2 * comp_genetica)
        return indice >= 70


@dataclass
class Familia:
    id_familia: str
    nombre: str
    miembros: Dict[str, Persona] = field(default_factory=dict)  # cedula -> Persona

    def agregar_persona(self, p: Persona):
        self.miembros[p.cedula] = p

    def obtener(self, cedula: str) -> Optional[Persona]:
        return self.miembros.get(cedula)

    def todas_personas(self) -> List[Persona]:
        return list(self.miembros.values())


class ArbolGenealogico:
    """Gestor de familias y relaciones (modelo y consultas)."""
    def __init__(self):
        self.familias: Dict[str, Familia] = {}
        # Reloj simulado
        self.fecha_simulada: date = hoy()

    # ---- Gestión familias ----
    def crear_familia(self, id_familia: str, nombre: str):
        if id_familia in self.familias:
            raise ValueError("ID de familia ya existe")
        self.familias[id_familia] = Familia(id_familia, nombre)

    def get_familia(self, id_familia: str) -> Optional[Familia]:
        return self.familias.get(id_familia)

    # ---- Gestión personas ----
    def agregar_persona(self, id_familia: str, persona: Persona):
        fam = self.get_familia(id_familia)
        if not fam:
            raise ValueError("Familia no existe")
        if persona.cedula in fam.miembros:
            raise ValueError("Cédula ya existe en la familia")
        # Afinidades: garantizar al menos 2 si vienen vacías
        if len(persona.afinidades) < 2:
            persona.afinidades.update(random.sample(AFINIDADES, 2))
        fam.agregar_persona(persona)
        persona.registrar_evento("Nacimiento", persona.fecha_nacimiento)

    # ---- Relaciones ----
    def unir_pareja(self, id_familia: str, ced1: str, ced2: str):
        fam = self.get_familia(id_familia)
        if not fam:
            return False
        a, b = fam.obtener(ced1), fam.obtener(ced2)
        if not a or not b:
            return False
        if not a.es_compatible_para_union(b):
            return False
        a.parejas.add(b.cedula)
        b.parejas.add(a.cedula)
        a.estado_civil = "Unión libre"
        b.estado_civil = "Unión libre"
        a.registrar_evento(f"Unión de pareja con {b.nombre}")
        b.registrar_evento(f"Unión de pareja con {a.nombre}")
        return True

    def registrar_matrimonio(self, id_familia: str, ced1: str, ced2: str) -> bool:
        fam = self.get_familia(id_familia)
        if not fam:
            return False
        a, b = fam.obtener(ced1), fam.obtener(ced2)
        if not a or not b:
            return False
        if b.cedula not in a.parejas:
            # Primero deben estar unidos
            if not self.unir_pareja(id_familia, ced1, ced2):
                return False
        a.estado_civil = "Casado(a)"
        b.estado_civil = "Casado(a)"
        a.registrar_evento(f"Matrimonio con {b.nombre}")
        b.registrar_evento(f"Matrimonio con {a.nombre}")
        return True

    def registrar_padre_hijo(self, id_familia: str, ced_padre: str, ced_hijo: str):
        fam = self.get_familia(id_familia)
        if not fam:
            return False
        padre, hijo = fam.obtener(ced_padre), fam.obtener(ced_hijo)
        if not padre or not hijo:
            return False
        hijo.padres.add(padre.cedula)
        padre.hijos.add(hijo.cedula)
        return True

    def registrar_nacimiento_de_pareja(self, id_familia: str, ced1: str, ced2: str) -> Optional[Persona]:
        fam = self.get_familia(id_familia)
        if not fam:
            return None
        a, b = fam.obtener(ced1), fam.obtener(ced2)
        if not a or not b:
            return None
        if b.cedula not in a.parejas:
            return None
        # Nuevo hijo
        new_ced = str(random.randint(10_000_000, 99_999_999))
        nombre = random.choice(["Alex", "Sam", "Pat", "Luz", "Mar", "Ari", "Noa", "Kai"])
        genero = random.choice(["Masculino", "Femenino"])  # binario por simplicidad
        provincia = random.choice([a.provincia, b.provincia])
        p = Persona(
            cedula=new_ced,
            nombre=nombre,
            fecha_nacimiento=self.fecha_simulada,
            genero=genero,
            provincia=provincia,
            estado_civil="Soltero(a)",
        )
        self.agregar_persona(id_familia, p)
        # Asociar con ambos padres
        p.padres.update({a.cedula, b.cedula})
        a.hijos.add(p.cedula)
        b.hijos.add(p.cedula)
        a.registrar_evento(f"Nacimiento de hijo/a {p.nombre}")
        b.registrar_evento(f"Nacimiento de hijo/a {p.nombre}")
        return p

    # ---- Efectos colaterales ----
    def gestionar_viudez(self, fam: Familia, persona_fallecida: Persona):
        for ced in list(persona_fallecida.parejas):
            pareja = fam.obtener(ced)
            if pareja and pareja.vivo:
                pareja.estado_civil = "Viudo(a)"
                pareja.parejas.discard(persona_fallecida.cedula)
                pareja.registrar_evento("Quedó viudo(a)")
                # Probabilidad menor de volver a unirse: bajar algo salud emocional
                pareja.salud_emocional = max(0, pareja.salud_emocional - 10)

    def reasignar_tutoria_menores(self, fam: Familia):
        # Si mueren madre y padre de un menor (<18), asignar tutor: tía/o, abuela/o si existe
        for p in fam.todas_personas():
            if not p.vivo:
                continue
            if p.edad(self.fecha_simulada) < 18:
                # Verificar estado de sus padres
                padres = [fam.obtener(c) for c in p.padres]
                if padres and all((pp and not pp.vivo) for pp in padres):
                    # buscar tutor (tío/tía = hermanos de los padres) o abuelos (padres de los padres)
                    candidatos: List[Persona] = []
                    for pp in padres:
                        if not pp:
                            continue
                        # hermanos de pp = personas que comparten al menos un padre con pp
                        for q in fam.todas_personas():
                            if q.cedula == pp.cedula or not q.vivo:
                                continue
                            if q.padres and q.padres.intersection(pp.padres):
                                candidatos.append(q)
                        # abuelos
                        for ced_ab in pp.padres:
                            ab = fam.obtener(ced_ab)
                            if ab and ab.vivo:
                                candidatos.append(ab)
                    if candidatos:
                        tutor = max(candidatos, key=lambda r: r.edad(self.fecha_simulada))
                        p.registrar_evento(f"Tutor legal asignado: {tutor.nombre}")

    # ---- Búsquedas ----
    def relacion_entre(self, fam: Familia, ced_a: str, ced_b: str) -> str:
        a, b = fam.obtener(ced_a), fam.obtener(ced_b)
        if not a or not b:
            return "No encontrado"
        if b.cedula in a.parejas:
            return "Pareja"
        if b.cedula in a.hijos:
            return "Padre/Madre de B"
        if a.cedula in b.hijos:
            return "Hijo(a) de B"
        # hermanos: comparten al menos un padre
        if a.padres and b.padres and a.padres.intersection(b.padres):
            return "Hermanos(as)"
        # primo: padres son hermanos
        padres_a = [fam.obtener(c) for c in a.padres]
        padres_b = [fam.obtener(c) for c in b.padres]
        for pa in padres_a:
            for pb in padres_b:
                if pa and pb and pa.padres and pb.padres and pa.padres.intersection(pb.padres):
                    return "Primos(as) de primer grado"
        return "Relación lejana o no directa"

    def primos_primer_grado(self, fam: Familia, ced_x: str) -> List[Persona]:
        x = fam.obtener(ced_x)
        if not x:
            return []
        primos = []
        # hijos de hermanos de los padres de X
        for ced_padre in x.padres:
            padre = fam.obtener(ced_padre)
            if not padre:
                continue
            # hermanos del padre = comparten al menos un progenitor
            hermanos_padre = [q for q in fam.todas_personas() if q.cedula != padre.cedula and q.padres and padre.padres.intersection(q.padres)]
            for tio in hermanos_padre:
                for ced_sobr in tio.hijos:
                    sob = fam.obtener(ced_sobr)
                    if sob:
                        primos.append(sob)
        # eliminar duplicados preservando orden
        vistos = set()
        res = []
        for p in primos:
            if p.cedula not in vistos:
                res.append(p)
                vistos.add(p.cedula)
        return res

    def antepasados_maternos(self, fam: Familia, ced_x: str) -> List[Persona]:
        x = fam.obtener(ced_x)
        if not x:
            return []
        res = []
        # suponer primer elemento de padres como madre si existe, de lo contrario cualquiera
        madre: Optional[Persona] = None
        for ced in x.padres:
            p = fam.obtener(ced)
            if p and p.genero == "Femenino":
                madre = p
                break
        if madre is None and x.padres:
            madre = fam.obtener(next(iter(x.padres)))
        cur = madre
        while cur:
            res.append(cur)
            # madre de la madre
            next_madre = None
            for ced in cur.padres:
                p = fam.obtener(ced)
                if p and p.genero == "Femenino":
                    next_madre = p
                    break
            if next_madre is None:
                # si no hay explícita, tomar cualquiera
                if cur.padres:
                    next_madre = fam.obtener(next(iter(cur.padres)))
            cur = next_madre
        return res

    def descendientes_vivos(self, fam: Familia, ced_x: str) -> List[Persona]:
        x = fam.obtener(ced_x)
        if not x:
            return []
        res = []
        stack = list(x.hijos)
        while stack:
            ced = stack.pop()
            p = fam.obtener(ced)
            if p:
                if p.vivo:
                    res.append(p)
                stack.extend(p.hijos)
        return res

    def nacidos_ultimos_10_anios(self, fam: Familia) -> List[Persona]:
        cutoff = self.fecha_simulada.replace(year=self.fecha_simulada.year - 10)
        return [p for p in fam.todas_personas() if p.fecha_nacimiento >= cutoff]

    def parejas_con_mas_de_dos_hijos(self, fam: Familia) -> List[Tuple[Persona, Persona]]:
        res = []
        vistos = set()
        for p in fam.todas_personas():
            for ced_par in p.parejas:
                if (p.cedula, ced_par) in vistos or (ced_par, p.cedula) in vistos:
                    continue
                pareja = fam.obtener(ced_par)
                if not pareja:
                    continue
                hijos_comunes = p.hijos.intersection(pareja.hijos)
                if len(hijos_comunes) >= 2:
                    res.append((p, pareja))
                vistos.add((p.cedula, ced_par))
        return res

    def fallecidos_antes_de_50(self, fam: Familia) -> List[Persona]:
        res = []
        for p in fam.todas_personas():
            if p.fecha_fallecimiento:
                if anios_entre(p.fecha_nacimiento, p.fecha_fallecimiento) < 50:
                    res.append(p)
        return res

    # ---- Simulación temporal y eventos cada 10s ----
    def tick_diario(self, dias: int = 1):
        # Avanza la fecha simulada
        self.fecha_simulada += timedelta(days=dias)

    def evento_cada_10s(self, id_familia: str):
        fam = self.get_familia(id_familia)
        if not fam:
            return
        # 1) Cumpleaños: +1 año en fecha de nacimiento -> lo simulamos aumentando un día
        self.tick_diario(365)  # avanzar un año de una sola vez por practicidad
        # 2) Fallecimientos aleatorios (solo vivos)
        for p in fam.todas_personas():
            if not p.vivo:
                continue
            # probabilidad base de muerte varía según edad + salud emocional
            base = 0.001 + (p.edad(self.fecha_simulada) / 1200.0)  # crece con la edad
            base += (50 - p.salud_emocional) / 10000.0
            if random.random() < base:
                p.marcar_fallecido(self.fecha_simulada)
                self.gestionar_viudez(fam, p)
        # 3) Uniones de pareja posibles
        vivos = [q for q in fam.todas_personas() if q.vivo]
        random.shuffle(vivos)
        for i in range(0, len(vivos), 2):
            if i + 1 < len(vivos):
                a, b = vivos[i], vivos[i + 1]
                # Menor prob si viudos recientemente (simulamos con estado civil)
                if a.estado_civil in ("Soltero(a)", "Divorciado(a)", "Viudo(a)") and \
                   b.estado_civil in ("Soltero(a)", "Divorciado(a)", "Viudo(a)"):
                    if a.es_compatible_para_union(b) and random.random() < 0.25:
                        self.unir_pareja(id_familia, a.cedula, b.cedula)
        # 4) Nacimientos en parejas compatibles
        parejas = []
        for p in fam.todas_personas():
            for ced_par in p.parejas:
                if p.cedula < ced_par:  # evitar duplicado de tuplas
                    parejas.append((p, fam.obtener(ced_par)))
        for a, b in parejas:
            if not a or not b:
                continue
            # Prob de tener hijo menor con la edad y estado civil (casados/unión libre)
            if a.edad(self.fecha_simulada) <= 45 and b.edad(self.fecha_simulada) <= 45:
                if random.random() < 0.15:
                    self.registrar_nacimiento_de_pareja(id_familia, a.cedula, b.cedula)
        # 5) Efectos colaterales
        self.reasignar_tutoria_menores(fam)


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

        # Modelo
        self.modelo = ArbolGenealogico()

        # Estado
        self.familia_activa: Optional[str] = None
        self.segundos = 0

        # Layout minimalista: sidebar + main
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.main = ctk.CTkFrame(self)
        self.main.pack(side="right", fill="both", expand=True)

        # Sidebar content
        self._build_sidebar()

        # Main views (stack)
        self.frames: Dict[str, tk.Frame] = {}
        self._build_views()

        # Tick
        self.after(self.REFRESH_MS, self._tick)

    # ---------------- Sidebar ----------------
    def _build_sidebar(self):
        title = ctk.CTkLabel(self.sidebar, text="Árbol\nGenealógico", justify="left", font=("Segoe UI", 20, "bold"))
        title.pack(padx=20, pady=(20, 10), anchor="w")

        self.lbl_familia = ctk.CTkLabel(self.sidebar, text="(sin familia)", font=("Segoe UI", 12))
        self.lbl_familia.pack(padx=20, pady=(0, 20), anchor="w")

        def add_btn(text, cmd):
            b = ctk.CTkButton(self.sidebar, text=text, command=cmd, corner_radius=12)
            b.pack(fill="x", padx=16, pady=6)
            return b

        add_btn("Familias", lambda: self._show("familias"))
        add_btn("Personas", lambda: self._show("personas"))
        add_btn("Relaciones", lambda: self._show("relaciones"))
        add_btn("Árbol", lambda: self._show("arbol"))
        add_btn("Búsquedas", lambda: self._show("busquedas"))
        add_btn("Historial", lambda: self._show("historial"))

        self.lbl_tiempo = ctk.CTkLabel(self.sidebar, text="Tiempo: 0s", font=("Segoe UI", 11))
        self.lbl_tiempo.pack(padx=16, pady=(16, 6), anchor="w")

        self.lbl_fecha = ctk.CTkLabel(self.sidebar, text=f"Fecha sim.: {hoy().isoformat()}", font=("Segoe UI", 11))
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
        frame = ctk.CTkFrame(parent)
        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(top, text="Gestión de familias", font=("Segoe UI", 18, "bold")).pack(anchor="w")

        form = ctk.CTkFrame(frame)
        form.pack(fill="x", padx=16, pady=(0, 16))

        self.id_fam_var = tk.StringVar()
        self.nom_fam_var = tk.StringVar()
        ctk.CTkEntry(form, placeholder_text="ID familia", textvariable=self.id_fam_var).pack(side="left", padx=6)
        ctk.CTkEntry(form, placeholder_text="Nombre familia", textvariable=self.nom_fam_var, width=240).pack(side="left", padx=6)
        ctk.CTkButton(form, text="Crear", command=self._crear_familia).pack(side="left", padx=6)

        listf = ctk.CTkFrame(frame)
        listf.pack(fill="both", expand=True, padx=16, pady=16)
        self.lst_familias = tk.Listbox(listf)
        self.lst_familias.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(listf, command=self.lst_familias.yview)
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
        frame = ctk.CTkFrame(parent)

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(top, text="Integrantes de familia", font=("Segoe UI", 18, "bold")).pack(anchor="w")

        form = ctk.CTkFrame(frame)
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
        ctk.CTkEntry(row1, placeholder_text="Cédula", textvariable=self.ced_var, width=120).pack(side="left", padx=4)
        ctk.CTkEntry(row1, placeholder_text="Nombre", textvariable=self.nom_var, width=200).pack(side="left", padx=4)
        ctk.CTkEntry(row1, placeholder_text="YYYY-MM-DD", textvariable=self.fnac_var, width=120).pack(side="left", padx=4)
        ctk.CTkOptionMenu(row1, values=GENEROS, variable=self.gen_var, width=140).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(form)
        row2.pack(fill="x", pady=4)
        ctk.CTkOptionMenu(row2, values=PROVINCIAS_CR, variable=self.prov_var, width=160).pack(side="left", padx=4)
        ctk.CTkOptionMenu(row2, values=ESTADOS_CIVILES, variable=self.eciv_var, width=160).pack(side="left", padx=4)
        ctk.CTkOptionMenu(row2, values=AFINIDADES, variable=self.af1_var, width=160).pack(side="left", padx=4)
        ctk.CTkOptionMenu(row2, values=AFINIDADES, variable=self.af2_var, width=160).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Agregar persona", command=self._agregar_persona).pack(side="left", padx=8)

        mid = ctk.CTkFrame(frame)
        mid.pack(fill="both", expand=True, padx=16, pady=16)
        self.lst_personas = tk.Listbox(mid)
        self.lst_personas.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(mid, command=self.lst_personas.yview)
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
        frame = ctk.CTkFrame(parent)
        ctk.CTkLabel(frame, text="Relaciones", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=16)

        # Uniones
        sec_union = ctk.CTkFrame(frame)
        sec_union.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(sec_union, text="Unir pareja / Matrimonio").pack(side="left")
        self.ced_a_var = tk.StringVar()
        self.ced_b_var = tk.StringVar()
        ctk.CTkEntry(sec_union, placeholder_text="Cédula A", textvariable=self.ced_a_var, width=120).pack(side="left", padx=6)
        ctk.CTkEntry(sec_union, placeholder_text="Cédula B", textvariable=self.ced_b_var, width=120).pack(side="left", padx=6)
        ctk.CTkButton(sec_union, text="Unir pareja", command=self._unir_pareja).pack(side="left", padx=6)
        ctk.CTkButton(sec_union, text="Matrimonio", command=self._matrimonio).pack(side="left", padx=6)

        # Padre-Hijo
        sec_ph = ctk.CTkFrame(frame)
        sec_ph.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(sec_ph, text="Registrar parentesco padre/madre ↔ hijo(a)").pack(side="left")
        self.ced_padre_var = tk.StringVar()
        self.ced_hijo_var = tk.StringVar()
        ctk.CTkEntry(sec_ph, placeholder_text="Cédula padre/madre", textvariable=self.ced_padre_var, width=160).pack(side="left", padx=6)
        ctk.CTkEntry(sec_ph, placeholder_text="Cédula hijo(a)", textvariable=self.ced_hijo_var, width=140).pack(side="left", padx=6)
        ctk.CTkButton(sec_ph, text="Vincular", command=self._padre_hijo).pack(side="left", padx=6)

        # Nacimiento de pareja
        sec_nac = ctk.CTkFrame(frame)
        sec_nac.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(sec_nac, text="Hijo(a) de la pareja").pack(side="left")
        self.ced_pa_var = tk.StringVar()
        self.ced_pb_var = tk.StringVar()
        ctk.CTkEntry(sec_nac, placeholder_text="Cédula A", textvariable=self.ced_pa_var, width=120).pack(side="left", padx=6)
        ctk.CTkEntry(sec_nac, placeholder_text="Cédula B", textvariable=self.ced_pb_var, width=120).pack(side="left", padx=6)
        ctk.CTkButton(sec_nac, text="Registrar nacimiento", command=self._nacimiento_pareja).pack(side="left", padx=6)

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
        frame = ctk.CTkFrame(parent)
        ctk.CTkLabel(frame, text="Árbol genealógico", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=16)
        self.canvas_arbol = tk.Canvas(frame, bg="#0f1115", highlightthickness=0)
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
        h = self.canvas_arbol.winfo_height() or 500
        box_w, box_h = 150, 40
        vgap = 80
        colors = {True: "#1f6aa5", False: "#444444"}

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
                self.canvas_arbol.create_rectangle(x, y, x + box_w, y + box_h, fill=colors[p.vivo], outline="#222", width=1)
                self.canvas_arbol.create_text(x + 8, y + 8, anchor="nw", fill="#e5e7eb", font=("Segoe UI", 11, "bold"), text=p.nombre)
                self.canvas_arbol.create_text(x + 8, y + 24, anchor="nw", fill="#a9b1bc", font=("Segoe UI", 9), text=f"{p.edad(self.modelo.fecha_simulada)} años")
        # líneas padres → hijos
        for p in fam.todas_personas():
            for h in p.hijos:
                if p.cedula in pos and h in pos:
                    x1, y1 = pos[p.cedula]
                    x2, y2 = pos[h]
                    self.canvas_arbol.create_line(x1 + box_w // 2, y1 + box_h, x2 + box_w // 2, y2, fill="#6b7280")

    # ---------------- View: Búsquedas ----------------
    def _view_busquedas(self, parent) -> tk.Frame:
        frame = ctk.CTkFrame(parent)
        ctk.CTkLabel(frame, text="Consultas", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=16)

        def row(label):
            rf = ctk.CTkFrame(frame)
            rf.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(rf, text=label, width=260, anchor="w").pack(side="left")
            e1, e2 = tk.StringVar(), tk.StringVar()
            c1 = ctk.CTkEntry(rf, placeholder_text="Cédula A", textvariable=e1, width=160)
            c2 = ctk.CTkEntry(rf, placeholder_text="Cédula B", textvariable=e2, width=160)
            c1.pack(side="left", padx=4)
            c2.pack(side="left", padx=4)
            out = ctk.CTkLabel(rf, text="", anchor="w")
            out.pack(side="left", padx=8)
            return e1, e2, out

        # 1 relación A-B
        self.q1_a, self.q1_b, self.q1_out = row("1) Relación entre A y B")
        ctk.CTkButton(frame, text="Consultar 1", command=self._q1).pack(anchor="w", padx=16)

        # 2 primos de X
        rf2 = ctk.CTkFrame(frame)
        rf2.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf2, text="2) Primos de primer grado de X", width=260, anchor="w").pack(side="left")
        self.q2_x = tk.StringVar()
        ctk.CTkEntry(rf2, placeholder_text="Cédula X", textvariable=self.q2_x, width=160).pack(side="left", padx=4)
        self.q2_out = ctk.CTkLabel(rf2, text="", anchor="w")
        self.q2_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 2", command=self._q2).pack(anchor="w", padx=16)

        # 3 antepasados maternos
        rf3 = ctk.CTkFrame(frame)
        rf3.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf3, text="3) Antepasados maternos de X", width=260, anchor="w").pack(side="left")
        self.q3_x = tk.StringVar()
        ctk.CTkEntry(rf3, placeholder_text="Cédula X", textvariable=self.q3_x, width=160).pack(side="left", padx=4)
        self.q3_out = ctk.CTkLabel(rf3, text="", anchor="w")
        self.q3_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 3", command=self._q3).pack(anchor="w", padx=16)

        # 4 descendientes vivos
        rf4 = ctk.CTkFrame(frame)
        rf4.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf4, text="4) Descendientes vivos de X", width=260, anchor="w").pack(side="left")
        self.q4_x = tk.StringVar()
        ctk.CTkEntry(rf4, placeholder_text="Cédula X", textvariable=self.q4_x, width=160).pack(side="left", padx=4)
        self.q4_out = ctk.CTkLabel(rf4, text="", anchor="w")
        self.q4_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 4", command=self._q4).pack(anchor="w", padx=16)

        # 5 nacidos últimos 10 años
        rf5 = ctk.CTkFrame(frame)
        rf5.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf5, text="5) ¿Cuántos nacieron en los últimos 10 años?", width=260, anchor="w").pack(side="left")
        self.q5_out = ctk.CTkLabel(rf5, text="", anchor="w")
        self.q5_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 5", command=self._q5).pack(anchor="w", padx=16)

        # 6 parejas con 2+ hijos
        rf6 = ctk.CTkFrame(frame)
        rf6.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf6, text="6) Parejas con 2+ hijos", width=260, anchor="w").pack(side="left")
        self.q6_out = ctk.CTkLabel(rf6, text="", anchor="w")
        self.q6_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 6", command=self._q6).pack(anchor="w", padx=16)

        # 7 fallecidos < 50
        rf7 = ctk.CTkFrame(frame)
        rf7.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(rf7, text="7) Fallecidos antes de 50 años", width=260, anchor="w").pack(side="left")
        self.q7_out = ctk.CTkLabel(rf7, text="", anchor="w")
        self.q7_out.pack(side="left", padx=8)
        ctk.CTkButton(frame, text="Consultar 7", command=self._q7).pack(anchor="w", padx=16)

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
        frame = ctk.CTkFrame(parent)
        ctk.CTkLabel(frame, text="Historial y línea del tiempo", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=16)

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=16, pady=6)
        self.hist_ced_var = tk.StringVar()
        ctk.CTkEntry(top, placeholder_text="Cédula", textvariable=self.hist_ced_var, width=180).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Ver historial", command=self._refrescar_historial).pack(side="left", padx=6)

        self.txt_hist = tk.Text(frame, height=14, bg="#0f1115", fg="#e5e7eb", insertbackground="#e5e7eb", relief="flat")
        self.txt_hist.pack(fill="both", expand=True, padx=16, pady=10)

        # Timeline visual simple
        self.canvas_timeline = tk.Canvas(frame, height=120, bg="#0f1115", highlightthickness=0)
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
            self.canvas_timeline.create_line(margin, 60, w - margin, 60, fill="#6b7280")
            span = max(1, y_max - y_min)
            for anio, ev in sorted(p.historial):
                x = margin + int((w - 2 * margin) * (anio - y_min) / span)
                self.canvas_timeline.create_oval(x - 4, 56, x + 4, 64, fill="#1f6aa5", outline="")
                self.canvas_timeline.create_text(x, 75, text=str(anio), fill="#a9b1bc", font=("Segoe UI", 9))
                self.canvas_timeline.create_text(x, 95, text=ev, fill="#e5e7eb", font=("Segoe UI", 9))

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
    # Semilla de ejemplo opcional (se puede borrar para la entrega)
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
