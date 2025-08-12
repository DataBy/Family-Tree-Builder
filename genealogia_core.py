# -*- coding: utf-8 -*-
"""
Módulo backend (lógica) para Árbol Genealógico.

Contiene únicamente el MODELO y reglas de negocio:
- Datos base (provincias, estados civiles, géneros, afinidades)
- Utilidades de fecha
- Dataclasses: Persona, Familia
- Gestor: ArbolGenealogico (CRUD, relaciones, búsquedas, simulación)

No depende de Tkinter ni CustomTkinter. Pensado para importarse desde
la interfaz (frontend) como:

    from genealogia_core import (
        Persona, Familia, ArbolGenealogico,
        PROVINCIAS_CR, ESTADOS_CIVILES, GENEROS, AFINIDADES,
        hoy
    )

Autor: ChatGPT
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import date, timedelta
import random

# ------------------------------- Datos base (listas para formularios) -------------------------------
PROVINCIAS_CR = [
    "San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón"
]
ESTADOS_CIVILES = [
    "Soltero(a)", "Casado(a)", "Unión libre", "Viudo(a)", "Divorciado(a)"
]
GENEROS = ["Masculino", "Femenino", "Otro"]

# Afinidades (mínimo 2 por persona)
AFINIDADES = [
    "Deporte", "Arte", "Ciencia", "Música", "Lectura", "Viajes", "Gastronomía", "Videojuegos"
]

# ------------------------------- Utilidades de fecha -------------------------------

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

# ------------------------------- Modelo de dominio -------------------------------

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


__all__ = [
    "Persona", "Familia", "ArbolGenealogico",
    "PROVINCIAS_CR", "ESTADOS_CIVILES", "GENEROS", "AFINIDADES",
    "hoy", "anios_entre"
]
