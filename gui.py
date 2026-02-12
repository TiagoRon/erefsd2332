import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from main import run_batch
import sys
import queue

class App: 
    def __init__(self, root):
        self.root = root
        self.root.title("AutoShorts Generator AI")
        self.root.geometry("600x500")
        self.root.configure(bg="#1e1e1e")

        # Thread-safe communication
        self.queue = queue.Queue()
        self.check_queue()

        #Center
        ancho_ventana =root.winfo_reqwidth()
        alto_ventana = root.winfo_reqheight()
        x = (root.winfo_screenwidth() // 2) - (ancho_ventana // 2 + 200) 
        y = (root.winfo_screenheight() // 2) - (alto_ventana // 2 + 200) 
        root.geometry(f'+{x}+{y}')
        root.resizable(0,0)

        # Header
        self.header = tk.Label(root, text="🚀 AutoShorts Generator", font=("Arial", 20, "bold"), bg="#1e1e1e", fg="#00ff9d")
        self.header.pack(pady=20)

        # Controls
        frame_controls = tk.Frame(root, bg="#1e1e1e")
        frame_controls.pack(pady=10)

        tk.Label(frame_controls, text="Cantidad de videos:", font=("Arial", 12), bg="#1e1e1e", fg="white").pack(side=tk.LEFT, padx=10)
        
        self.entry_count = tk.Entry(frame_controls, width=5, font=("Arial", 12))
        self.entry_count.insert(0, "1")
        self.entry_count.pack(side=tk.LEFT, padx=10)

        # Mode Selection (Radio)
        tk.Label(frame_controls, text="Modo:", font=("Arial", 12), bg="#1e1e1e", fg="white").pack(side=tk.LEFT, padx=10)
        
        self.var_mode = tk.StringVar(value="curiosity")
        
        rb_curiosity = tk.Radiobutton(frame_controls, text="Curiosidad", variable=self.var_mode, value="curiosity", 
                                      font=("Arial", 10), bg="#1e1e1e", fg="orange", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="orange")
        rb_curiosity.pack(side=tk.LEFT, padx=2)
        
        rb_whatif = tk.Radiobutton(frame_controls, text="What If", variable=self.var_mode, value="what_if", 
                                   font=("Arial", 10), bg="#1e1e1e", fg="cyan", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="cyan")
        rb_whatif.pack(side=tk.LEFT, padx=2)

        rb_top3 = tk.Radiobutton(frame_controls, text="Top 3", variable=self.var_mode, value="top_3", 
                                 font=("Arial", 10), bg="#1e1e1e", fg="#ADFF2F", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="#ADFF2F")
        rb_top3.pack(side=tk.LEFT, padx=2)

        self.btn_run = tk.Button(frame_controls, text="GENERAR ▶", font=("Arial", 12, "bold"), bg="#00bcff", fg="white", cursor="hand2", command=self.start_generation)
        self.btn_run.pack(side=tk.LEFT, padx=20)

        # Log Area
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=20, font=("Consolas", 10), bg="#2d2d2d", fg="#d4d4d4", wrap=tk.WORD)
        self.log_area.pack(pady=20, padx=20)
        self.log("Bienvenido. Ingresa la cantidad y pulsa Generar.")

    def check_queue(self):
        try:
            while True:
                msg_type, content = self.queue.get_nowait()
                if msg_type == 'log':
                    self.log_area.insert(tk.END, str(content) + "\n")
                    self.log_area.see(tk.END)
                elif msg_type == 'status_done':
                     self.btn_run.config(state=tk.NORMAL, text="GENERAR ▶")
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def log(self, message):
        self.queue.put(('log', message))

    def start_generation(self):
        try:
            count = int(self.entry_count.get())
            if count < 1: 
                messagebox.showerror("Error", "El número debe ser mayor a 0")
                return
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número válido")
            return

        self.btn_run.config(state=tk.DISABLED, text="Generando... ⏳")
        self.log(f"\n⚡ Iniciando generación de {count} videos...")
        
        mode = self.var_mode.get()
        use_trends = (mode == "curiosity") # Trends logic applies to default curiosity for now, or we can separate it.
        # Simplification: 'Trends' was mixing with Curiosity. Now we just pass style.
        
        # Thread to avoid freezing UI
        t = threading.Thread(target=self.run_process, args=(count, mode))
        t.start()

    def run_process(self, count, mode):
        try:
            # Determine style
            style = mode
            use_trends = (mode == "curiosity") # Only pull trends for curiosity mode for now
            
            # Call the main logic passing the log function
            run_batch(count, use_trends=use_trends, style=style, log_func=self.log)
            self.log("\n✅ ¡Proceso completado!")
        except Exception as e:
            self.log(f"\n❌ Error Fatal: {e}")
        finally:
            self.queue.put(('status_done', None))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
