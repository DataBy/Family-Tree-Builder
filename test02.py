# familytree_ctk.py
import datetime
import customtkinter as ctk
from PIL import Image

# ==== Config ====
WELCOME_IMG_PATH = "assets/backgrounds/home.png"   # 950x650
MENU_LOGO_PATH   = "assets/logos/FamilyTree.png"

COLOR_BG      = "#172033"  # fondo principal
COLOR_SURFACE = "#16324A"  # panel central
COLOR_ACCENT  = "#01C38E"  # botones/acento
TEXT_LIGHT    = "#E6F1F5"

WINDOW_W, WINDOW_H = 1366, 768
SIDEBAR_W = 190

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FamilyTree")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.minsize(1280, 720)
        self.configure(fg_color=COLOR_BG)

        # Grid base
        self.grid_columnconfigure(0, minsize=SIDEBAR_W)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

        # Tiempo
        self.start_time = datetime.datetime.now()
        self._tick_time()

    # ---------- Sidebar ----------
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_columnconfigure(0, weight=1)

        # Logo superior
        logo_img = self._safe_image(MENU_LOGO_PATH, size=(326, 90))
        logo = ctk.CTkLabel(sb, text="", image=logo_img)
        logo.image = logo_img
        logo.grid(row=0, column=0, pady=(18, 8))

        # “Familia: ID” (20 px) con separación 24px debajo
        id_lbl = ctk.CTkLabel(sb, text="Familia: ID",
                              text_color=TEXT_LIGHT, font=("Inter", 20, "bold"))
        id_lbl.grid(row=1, column=0, pady=(0, 24))

        # Botones menú (24 px) con separación 24 px
        def mk_btn(text, r):
            btn = ctk.CTkButton(
                sb, text=text, fg_color=COLOR_ACCENT, hover_color="#00a87a",
                text_color="#0E1A24", font=("Inter", 24, "bold"),
                height=46, corner_radius=10
            )
            btn.grid(row=r, column=0, padx=16, pady=(0, 24), sticky="ew")
            return btn

        items = ["Familias", "Personas", "Relaciones", "Árbol",
                 "Búsquedas", "Historial", "Chatbot"]
        for i, t in enumerate(items, start=2):
            mk_btn(t, i)

        # Tiempo y fecha (20 px) con separación de 24px entre sí
        self.lbl_time = ctk.CTkLabel(sb, text="Tiempo: 0s",
                                     text_color=TEXT_LIGHT, font=("Inter", 20))
        self.lbl_time.grid(row=len(items)+3, column=0, pady=(0, 24))

        today = datetime.datetime.now().strftime("%d/%m/%Y")
        self.lbl_date = ctk.CTkLabel(sb, text=f"Fecha: {today}",
                                     text_color=TEXT_LIGHT, font=("Inter", 20))
        self.lbl_date.grid(row=len(items)+4, column=0, pady=(0, 20))

    # ---------- Main / Centro ----------
    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # Solo la imagen de bienvenida
        welcome_img = self._safe_image(WELCOME_IMG_PATH, size=(950, 650))
        self.lbl_welcome = ctk.CTkLabel(main, text="", image=welcome_img)
        self.lbl_welcome.image = welcome_img
        self.lbl_welcome.grid(row=0, column=0)

    # ---------- Utils ----------
    def _safe_image(self, path, size):
        try:
            img = Image.open(path).convert("RGBA")
            if size:
                img = img.resize(size, Image.LANCZOS)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            from PIL import ImageDraw, ImageFont
            ph = Image.new("RGBA", size, (22, 50, 74, 255))
            d = ImageDraw.Draw(ph)
            msg = "Imagen no encontrada"
            try:
                fnt = ImageFont.truetype("arial.ttf", 22)
            except Exception:
                fnt = None
            w, h = d.textbbox((0, 0), msg, font=fnt)[2:]
            d.text(((size[0]-w)//2, (size[1]-h)//2), msg,
                   fill=(230, 241, 245, 220), font=fnt)
            return ctk.CTkImage(light_image=ph, dark_image=ph, size=size)

    def _tick_time(self):
        elapsed = (datetime.datetime.now() - self.start_time).seconds
        self.lbl_time.configure(text=f"Tiempo: {elapsed}s")
        self.after(1000, self._tick_time)


if __name__ == "__main__":
    App().mainloop()
