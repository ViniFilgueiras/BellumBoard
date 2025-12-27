import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import random
import threading
import time

# Instalação necessária:
# pip install python-vlc yt-dlp requests

try:
    import vlc
except ImportError:
    print("ERRO: Instale python-vlc: pip install python-vlc")
    vlc = None

try:
    import yt_dlp
except ImportError:
    print("ERRO: Instale yt-dlp: pip install yt-dlp")
    yt_dlp = None

try:
    import requests
except ImportError:
    print("AVISO: Instale requests para importar playlists do Spotify: pip install requests")
    requests = None

class Track:
    def __init__(self, title: str, url: str, video_id: str, start_time: int = 0):
        self.title = title
        self.url = url
        self.video_id = video_id
        self.start_time = start_time  # em segundos
    
    def to_dict(self):
        return {
            'title': self.title,
            'url': self.url,
            'video_id': self.video_id,
            'start_time': self.start_time
        }
    
    @staticmethod
    def from_dict(data):
        return Track(
            data['title'],
            data['url'],
            data.get('video_id', ''),
            data.get('start_time', 0)
        )

class Playlist:
    def __init__(self, name: str, tracks: List[Track] = None):
        self.name = name
        self.tracks = tracks or []
    
    def add_track(self, track: Track):
        self.tracks.append(track)
    
    def remove_track(self, index: int):
        if 0 <= index < len(self.tracks):
            self.tracks.pop(index)
    
    def to_dict(self):
        return {
            'name': self.name,
            'tracks': [t.to_dict() for t in self.tracks]
        }
    
    @staticmethod
    def from_dict(data):
        tracks = [Track.from_dict(t) for t in data.get('tracks', [])]
        return Playlist(data['name'], tracks)

class MusicPlayer:
    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.player = None
        self.current_url = None
        self.is_playing = False
        self.volume = 70
        
        if vlc:
            self.instance = vlc.Instance('--no-xlib')
            self.player = self.instance.media_player_new()
            self.player.audio_set_volume(self.volume)
        else:
            self.status_callback("ERRO: VLC não instalado!")
    
    def play(self, url: str, start_time: int = 0):
        if not self.player:
            self.status_callback("Player não disponível")
            return False
        
        try:
            self.current_url = url
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
            
            # Aguarda o player iniciar antes de setar o tempo
            time.sleep(0.5)
            if start_time > 0:
                self.player.set_time(start_time * 1000)  # VLC usa milissegundos
            
            self.is_playing = True
            return True
        except Exception as e:
            self.status_callback(f"Erro ao tocar: {str(e)}")
            return False
    
    def pause(self):
        if self.player:
            self.player.pause()
            self.is_playing = not self.is_playing
    
    def stop(self):
        if self.player:
            self.player.stop()
            self.is_playing = False
            self.current_url = None
    
    def set_volume(self, volume: int):
        self.volume = max(0, min(100, volume))
        if self.player:
            self.player.audio_set_volume(self.volume)
    
    def get_state(self):
        if self.player:
            return self.player.get_state()
        return None
    
    def is_finished(self):
        if self.player:
            state = self.player.get_state()
            return state == vlc.State.Ended
        return False

class RPGSoundboard:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG Soundboard - YouTube Edition")
        self.root.geometry("1100x750")
        
        self.data_file = Path("soundboard_data.json")
        self.folders: Dict[str, List[Playlist]] = {}
        self.current_playlist: Optional[Playlist] = None
        self.current_track_index = 0
        self.shuffle_mode = False
        self.shuffle_queue = []
        self.auto_play = False
        self.search_results = []
        
        self.load_data()
        self.player = MusicPlayer(self.update_status)
        self.create_ui()
        
        # Salva dados ao fechar (configura depois de tudo inicializado)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Atualiza árvore após carregar dados
        self.root.after(100, self.update_tree)
        
        # Monitor para próxima música automática
        self.monitor_thread = threading.Thread(target=self.monitor_playback, daemon=True)
        self.monitor_thread.start()
    
    def create_ui(self):
        # Menu superior
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Nova Pasta", command=self.create_folder)
        file_menu.add_command(label="Nova Playlist", command=self.create_playlist)
        file_menu.add_separator()
        file_menu.add_command(label="Salvar", command=self.save_data)
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)
        
        # Frame principal dividido
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Painel esquerdo - Pastas e Playlists
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="📁 BellumBoard", font=('Arial', 12, 'bold')).pack(pady=5)
        
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_frame, selectmode='browse')
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Painel direito
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=2)
        
        # Busca YouTube
        search_frame = ttk.LabelFrame(right_frame, text="🔍 Adicionar Músicas", padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Busca por termo
        search_container = ttk.Frame(search_frame)
        search_container.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_container, text="Buscar:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_container, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', lambda e: self.search_music())
        
        ttk.Button(search_container, text="🔍 Buscar", command=self.search_music).pack(side=tk.LEFT, padx=5)
        
        # Adicionar por URL
        url_container = ttk.Frame(search_frame)
        url_container.pack(fill=tk.X)
        
        ttk.Label(url_container, text="URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(url_container, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.url_entry.bind('<Return>', lambda e: self.add_from_url())
        
        ttk.Button(url_container, text="➕ Adicionar URL", command=self.add_from_url).pack(side=tk.LEFT, padx=2)
        ttk.Button(url_container, text="📋 Importar Playlist Spotify", command=self.import_spotify_playlist).pack(side=tk.LEFT, padx=2)
        
        # Resultados da busca
        results_frame = ttk.LabelFrame(right_frame, text="Resultados", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        results_container = ttk.Frame(results_frame)
        results_container.pack(fill=tk.BOTH, expand=True)
        
        self.results_list = tk.Listbox(results_container, height=8)
        results_scroll = ttk.Scrollbar(results_container, orient=tk.VERTICAL, command=self.results_list.yview)
        self.results_list.configure(yscrollcommand=results_scroll.set)
        
        self.results_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_list.bind('<Double-1>', lambda e: self.add_to_playlist())
        
        ttk.Button(results_frame, text="➕ Adicionar à Playlist", command=self.add_to_playlist).pack(pady=5)
        
        # Playlist atual
        current_frame = ttk.LabelFrame(right_frame, text="🎵 Playlist Atual", padding=10)
        current_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.current_label = ttk.Label(current_frame, text="Nenhuma playlist selecionada", font=('Arial', 10, 'bold'))
        self.current_label.pack(pady=5)
        
        tracks_container = ttk.Frame(current_frame)
        tracks_container.pack(fill=tk.BOTH, expand=True)
        
        self.tracks_list = tk.Listbox(tracks_container, height=10)
        tracks_scroll = ttk.Scrollbar(tracks_container, orient=tk.VERTICAL, command=self.tracks_list.yview)
        self.tracks_list.configure(yscrollcommand=tracks_scroll.set)
        
        self.tracks_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tracks_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tracks_list.bind('<Double-1>', self.on_track_double_click)
        
        # Controles de reprodução
        control_frame = ttk.Frame(current_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="▶ Tocar", command=self.play_track, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⏸ Pausar", command=self.pause_track, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⏹ Parar", command=self.stop_track, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⏭ Próxima", command=self.next_track, width=10).pack(side=tk.LEFT, padx=2)
        
        # Opções de reprodução
        options_frame = ttk.Frame(current_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.shuffle_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="🔀 Aleatório", variable=self.shuffle_var, 
                       command=self.toggle_shuffle).pack(side=tk.LEFT, padx=5)
        
        self.auto_play_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="🔁 Auto-Play", variable=self.auto_play_var,
                       command=self.toggle_auto_play).pack(side=tk.LEFT, padx=5)
        
        # Volume
        ttk.Label(options_frame, text="🔊 Volume:").pack(side=tk.LEFT, padx=5)
        self.volume_scale = ttk.Scale(options_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     command=self.change_volume, length=150)
        self.volume_scale.set(70)
        self.volume_scale.pack(side=tk.LEFT, padx=5)
        
        self.volume_label = ttk.Label(options_frame, text="70%", width=5)
        self.volume_label.pack(side=tk.LEFT, padx=2)
        
        # Edição
        edit_frame = ttk.Frame(current_frame)
        edit_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(edit_frame, text="⏱ Definir Início", command=self.set_start_time).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_frame, text="🗑 Remover", command=self.remove_track).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_frame, text="⬆ Mover para Cima", command=self.move_track_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(edit_frame, text="⬇ Mover para Baixo", command=self.move_track_down).pack(side=tk.LEFT, padx=2)
        
        # Status
        self.status_label = ttk.Label(self.root, text="✅ Pronto - Busque músicas no YouTube", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.update_tree()
    
    def show_about(self):
        about_text = """RPG Soundboard - YouTube Edition
        
Versão 2.0

Crie playlists personalizadas para suas sessões de RPG!

Recursos:
• Busca no YouTube
• Adicionar músicas por URL
• Importar playlists do Spotify
• Reprodução interna
• Tempo de início customizável
• Modo aleatório
• Auto-play
• Organização em pastas

Dependências:
• python-vlc
• yt-dlp
• requests
• VLC Media Player

Desenvolvido para mestres de RPG"""
        
        messagebox.showinfo("Sobre", about_text)
    
    def search_music(self):
        query = self.search_entry.get().strip()
        
        if not query:
            messagebox.showwarning("Aviso", "Digite um termo de busca!")
            return
        
        if not yt_dlp:
            messagebox.showerror("Erro", "yt-dlp não está instalado!\npip install yt-dlp")
            return
        
        self.results_list.delete(0, tk.END)
        self.update_status(f"🔍 Buscando '{query}' no YouTube...")
        
        # Executa busca em thread separada
        thread = threading.Thread(target=self._search_thread, args=(query,))
        thread.start()
    
    def _search_thread(self, query: str):
        try:
            results = self.search_youtube(query)
            self.root.after(0, self._update_search_results, results)
        except Exception as e:
            self.root.after(0, self.update_status, f"❌ Erro na busca: {str(e)}")
    
    def search_youtube(self, query: str) -> List[Dict]:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch15'
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch15:{query}", download=False)
                entries = result.get('entries', [])
                
                return [
                    {
                        'title': entry.get('title', 'Sem título'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                        'video_id': entry.get('id', ''),
                        'duration': int(entry.get('duration', 0) or 0)  # Garante inteiro
                    }
                    for entry in entries[:15]
                ]
        except Exception as e:
            print(f"Erro YouTube: {e}")
            return []
    
    def _update_search_results(self, results: List[Dict]):
        self.search_results = results
        for i, result in enumerate(results):
            duration = self.format_duration(result.get('duration', 0))
            self.results_list.insert(tk.END, f"{i+1}. {result['title']} ({duration})")
        
        self.update_status(f"✅ {len(results)} resultado(s) encontrado(s)")
    
    def add_from_url(self):
        """Adiciona uma música diretamente por URL do YouTube"""
        print("add_from_url chamada!")  # Debug
        
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Selecione uma playlist primeiro!")
            return
        
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Digite uma URL!")
            return
        
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showerror("Erro", "URL deve ser do YouTube!")
            return
        
        self.update_status(f"⏳ Obtendo informações da URL...")
        thread = threading.Thread(target=self._add_url_thread, args=(url,))
        thread.start()
    
    def _add_url_thread(self, url: str):
        try:
            print(f"Tentando adicionar URL: {url}")  # Debug
            
            if not yt_dlp:
                self.root.after(0, messagebox.showerror, "Erro", "yt-dlp não instalado!")
                return
            
            # Remove parâmetros da URL (como ?list=...)
            if '?' in url:
                url = url.split('?')[0]
                print(f"URL limpa: {url}")  # Debug
            
            ydl_opts = {
                'quiet': False,  # Mostra logs para debug
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Extraindo informações...")  # Debug
                info = ydl.extract_info(url, download=False)
                
                print(f"Info obtida: {info.get('title', 'N/A')}")  # Debug
                
                track = Track(
                    info.get('title', 'Sem título'),
                    url,
                    info.get('id', ''),
                    0
                )
                
                print(f"Track criada: {track.title}")  # Debug
                print(f"Playlist atual: {self.current_playlist.name if self.current_playlist else 'None'}")  # Debug
                
                self.current_playlist.add_track(track)
                print(f"Track adicionada! Total na playlist: {len(self.current_playlist.tracks)}")  # Debug
                
                self.root.after(0, self.load_playlist, self.current_playlist)
                self.root.after(0, self.save_data)
                self.root.after(0, self.update_status, f"✅ Música adicionada: {track.title}")
                self.root.after(0, self.url_entry.delete, 0, tk.END)
                
                print("Concluído!")  # Debug
        
        except Exception as e:
            print(f"ERRO: {e}")  # Debug
            import traceback
            traceback.print_exc()  # Debug completo
            self.root.after(0, messagebox.showerror, "Erro", f"Erro ao adicionar URL:\n{str(e)}")
            self.root.after(0, self.update_status, "❌ Erro ao adicionar URL")
    
    def import_spotify_playlist(self):
        """Importa playlist do Spotify e busca músicas no YouTube"""
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Selecione uma playlist primeiro!")
            return
        
        url = self.url_entry.get().strip()
        if not url:
            url = simpledialog.askstring("Importar Playlist Spotify", 
                                         "Cole a URL da playlist do Spotify:")
        
        if not url:
            return
        
        if "spotify.com/playlist" not in url:
            messagebox.showerror("Erro", "URL deve ser de uma playlist do Spotify!\nExemplo: https://open.spotify.com/playlist/...")
            return
        
        # Extrai o ID da playlist
        try:
            playlist_id = url.split("playlist/")[1].split("?")[0]
        except:
            messagebox.showerror("Erro", "URL inválida!")
            return
        
        self.update_status(f"⏳ Importando playlist do Spotify...")
        thread = threading.Thread(target=self._import_spotify_thread, args=(playlist_id,))
        thread.start()
    
    def _import_spotify_thread(self, playlist_id: str):
        try:
            if not requests:
                self.root.after(0, messagebox.showerror, "Erro", 
                              "Biblioteca 'requests' não instalada!\npip install requests")
                return
            
            # Busca informações da playlist via API pública do Spotify
            self.root.after(0, self.update_status, f"📥 Obtendo músicas da playlist...")
            
            tracks = self.get_spotify_tracks(playlist_id)
            
            if not tracks:
                self.root.after(0, messagebox.showerror, "Erro", "Não foi possível obter as músicas da playlist")
                return
            
            self.root.after(0, self.update_status, f"🔍 Buscando {len(tracks)} músicas no YouTube...")
            
            # Busca cada música no YouTube
            added = 0
            for i, track_info in enumerate(tracks):
                try:
                    query = f"{track_info['name']} {track_info['artist']}"
                    results = self.search_youtube(query)
                    
                    if results:
                        # Adiciona o primeiro resultado
                        result = results[0]
                        track = Track(
                            f"{track_info['name']} - {track_info['artist']}",
                            result['url'],
                            result['video_id'],
                            0
                        )
                        self.current_playlist.add_track(track)
                        added += 1
                    
                    # Atualiza progresso
                    progress = f"🔍 Processando: {i+1}/{len(tracks)} - {added} encontradas"
                    self.root.after(0, self.update_status, progress)
                    
                except Exception as e:
                    print(f"Erro ao buscar {track_info['name']}: {e}")
            
            self.root.after(0, self.load_playlist, self.current_playlist)
            self.root.after(0, self.save_data)
            self.root.after(0, self.update_status, f"✅ {added}/{len(tracks)} músicas importadas com sucesso!")
            self.root.after(0, self.url_entry.delete, 0, tk.END)
            
            if added < len(tracks):
                msg = f"Importação concluída!\n\n{added} de {len(tracks)} músicas foram encontradas no YouTube."
                self.root.after(0, messagebox.showinfo, "Importação Concluída", msg)
        
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Erro", f"Erro ao importar playlist:\n{str(e)}")
            self.root.after(0, self.update_status, "❌ Erro ao importar playlist")
    
    def get_spotify_tracks(self, playlist_id: str) -> List[Dict]:
        """Obtém lista de músicas de uma playlist do Spotify usando API pública"""
        try:
            print(f"Buscando playlist do Spotify: {playlist_id}")  # Debug
            
            # Usa o endpoint público do Spotify
            url = f"https://open.spotify.com/playlist/{playlist_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status code: {response.status_code}")  # Debug
            
            if response.status_code != 200:
                print(f"Erro ao acessar Spotify: {response.status_code}")
                return []
            
            # Extrai dados do JSON embutido na página
            import re
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', 
                            response.text, re.DOTALL)
            
            if not match:
                print("Não encontrou __NEXT_DATA__")  # Debug
                # Tenta método alternativo: buscar no Spotify Embed API
                return self._get_spotify_tracks_embed(playlist_id)
            
            import json
            data = json.loads(match.group(1))
            print("JSON extraído com sucesso")  # Debug
            
            # Navega pela estrutura do JSON
            try:
                playlist_data = data['props']['pageProps']['state']['data']['entity']
                tracks = []
                
                items = playlist_data.get('tracks', {}).get('items', [])
                print(f"Encontradas {len(items)} músicas")  # Debug
                
                for item in items:
                    track = item.get('track', {})
                    if track and track.get('name'):
                        artists = ', '.join([artist.get('name', '') for artist in track.get('artists', [])])
                        tracks.append({
                            'name': track.get('name', ''),
                            'artist': artists
                        })
                
                return tracks
            except Exception as e:
                print(f"Erro ao navegar JSON: {e}")  # Debug
                return []
            
        except Exception as e:
            print(f"Erro ao obter tracks do Spotify: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_spotify_tracks_embed(self, playlist_id: str) -> List[Dict]:
        """Método alternativo usando Spotify Embed API"""
        try:
            print("Tentando método alternativo (Embed API)")
            # Este é um endpoint público do Spotify para embeds
            url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Procura por padrões de título e artista no HTML
            import re
            tracks = []
            
            # Regex para encontrar músicas (pode precisar ajustar dependendo da estrutura)
            pattern = r'"name":"([^"]+)".*?"artists":\[.*?"name":"([^"]+)"'
            matches = re.finditer(pattern, response.text)
            
            for match in matches:
                tracks.append({
                    'name': match.group(1),
                    'artist': match.group(2)
                })
            
            # Remove duplicatas
            seen = set()
            unique_tracks = []
            for track in tracks:
                key = f"{track['name']}|{track['artist']}"
                if key not in seen:
                    seen.add(key)
                    unique_tracks.append(track)
            
            print(f"Método alternativo encontrou {len(unique_tracks)} músicas")
            return unique_tracks[:50]  # Limita a 50 músicas
            
        except Exception as e:
            print(f"Erro no método alternativo: {e}")
            return []
    
        if seconds == 0:
            return "?"
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
    
    def add_to_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Selecione uma playlist primeiro!")
            return
        
        selection = self.results_list.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um resultado!")
            return
        
        idx = selection[0]
        result = self.search_results[idx]
        
        track = Track(
            result['title'],
            result['url'],
            result['video_id'],
            0
        )
        
        self.current_playlist.add_track(track)
        self.load_playlist(self.current_playlist)
        self.save_data()
        self.update_status(f"✅ '{result['title']}' adicionada à playlist")
    
    def get_youtube_stream_url(self, video_id: str) -> str:
        if not yt_dlp:
            return f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            ydl_opts = {
                'quiet': True,
                'format': 'bestaudio/best',
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info.get('url', '')
        except Exception as e:
            print(f"Erro ao obter stream: {e}")
            return ""
    
    def play_track(self):
        if not self.current_playlist or not self.current_playlist.tracks:
            messagebox.showwarning("Aviso", "Nenhuma música na playlist!")
            return
        
        selection = self.tracks_list.curselection()
        if selection:
            self.current_track_index = selection[0]
        
        # Thread para não travar interface
        thread = threading.Thread(target=self._play_track_thread)
        thread.start()
    
    def _play_track_thread(self):
        if self.shuffle_mode and self.shuffle_queue:
            actual_index = self.shuffle_queue[self.current_track_index]
        else:
            actual_index = self.current_track_index
        
        track = self.current_playlist.tracks[actual_index]
        
        self.root.after(0, self.update_status, f"⏳ Carregando: {track.title}...")
        
        # Obtém URL de streaming
        stream_url = self.get_youtube_stream_url(track.video_id)
        
        if not stream_url:
            self.root.after(0, self.update_status, f"❌ Erro ao carregar: {track.title}")
            return
        
        self.root.after(0, self.update_status, f"▶ Tocando: {track.title}")
        success = self.player.play(stream_url, track.start_time)
        
        if not success:
            self.root.after(0, self.update_status, f"❌ Erro ao tocar: {track.title}")
    
    def pause_track(self):
        self.player.pause()
        status = "▶ Retomado" if self.player.is_playing else "⏸ Pausado"
        self.update_status(status)
    
    def stop_track(self):
        self.player.stop()
        self.update_status("⏹ Parado")
    
    def next_track(self):
        if not self.current_playlist or not self.current_playlist.tracks:
            return
        
        if self.shuffle_mode:
            self.current_track_index = (self.current_track_index + 1) % len(self.shuffle_queue)
        else:
            self.current_track_index = (self.current_track_index + 1) % len(self.current_playlist.tracks)
        
        self.tracks_list.selection_clear(0, tk.END)
        actual_index = self.shuffle_queue[self.current_track_index] if self.shuffle_mode else self.current_track_index
        self.tracks_list.selection_set(actual_index)
        self.tracks_list.see(actual_index)
        
        self.play_track()
    
    def monitor_playback(self):
        while True:
            if self.auto_play and self.player.is_finished():
                self.root.after(0, self.next_track)
                time.sleep(2)
            time.sleep(1)
    
    def toggle_shuffle(self):
        self.shuffle_mode = self.shuffle_var.get()
        if self.shuffle_mode and self.current_playlist:
            self.generate_shuffle_queue()
            self.update_status("🔀 Modo aleatório ativado")
        else:
            self.update_status("➡ Modo sequencial ativado")
    
    def toggle_auto_play(self):
        self.auto_play = self.auto_play_var.get()
        status = "ativado" if self.auto_play else "desativado"
        self.update_status(f"🔁 Auto-play {status}")
    
    def change_volume(self, value):
        volume = int(float(value))
        self.player.set_volume(volume)
        if hasattr(self, 'volume_label'):
            self.volume_label.config(text=f"{volume}%")
    
    def generate_shuffle_queue(self):
        if self.current_playlist:
            self.shuffle_queue = list(range(len(self.current_playlist.tracks)))
            random.shuffle(self.shuffle_queue)
            self.current_track_index = 0
    
    def set_start_time(self):
        selection = self.tracks_list.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma música da playlist primeiro!")
            return
        
        idx = selection[0]
        current_time = self.current_playlist.tracks[idx].start_time
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Definir Tempo de Início")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Tempo de início em segundos:", font=('Arial', 10, 'bold')).pack(pady=15)
        ttk.Label(dialog, text="(Útil para pular intros ou ir direto ao ponto desejado)", font=('Arial', 8)).pack(pady=5)
        
        time_var = tk.IntVar(value=current_time)
        time_spinbox = ttk.Spinbox(dialog, from_=0, to=3600, textvariable=time_var, width=20)
        time_spinbox.pack(pady=10)
        time_spinbox.focus()
        
        def apply_time():
            try:
                time_val = time_var.get()
                if time_val < 0:
                    messagebox.showerror("Erro", "Digite um número positivo!")
                    return
                self.current_playlist.tracks[idx].start_time = time_val
                self.load_playlist(self.current_playlist)
                self.save_data()
                self.update_status(f"⏱ Tempo de início definido: {time_val}s")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Digite um número válido!")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Aplicar", command=apply_time).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        time_spinbox.bind('<Return>', lambda e: apply_time())
    
    def remove_track(self):
        selection = self.tracks_list.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma música!")
            return
        
        idx = selection[0]
        track_name = self.current_playlist.tracks[idx].title
        
        if messagebox.askyesno("Confirmar", f"Remover '{track_name}'?"):
            self.current_playlist.remove_track(idx)
            self.load_playlist(self.current_playlist)
            self.save_data()
            self.update_status(f"🗑 Música removida: {track_name}")
    
    def move_track_up(self):
        selection = self.tracks_list.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma música!")
            return
        
        idx = selection[0]
        if idx == 0:
            return
        
        tracks = self.current_playlist.tracks
        tracks[idx], tracks[idx-1] = tracks[idx-1], tracks[idx]
        self.load_playlist(self.current_playlist)
        self.tracks_list.selection_set(idx-1)
        self.save_data()
    
    def move_track_down(self):
        selection = self.tracks_list.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma música!")
            return
        
        idx = selection[0]
        if idx >= len(self.current_playlist.tracks) - 1:
            return
        
        tracks = self.current_playlist.tracks
        tracks[idx], tracks[idx+1] = tracks[idx+1], tracks[idx]
        self.load_playlist(self.current_playlist)
        self.tracks_list.selection_set(idx+1)
        self.save_data()
    
    def create_folder(self):
        name = simpledialog.askstring("Nova Pasta", "Nome da pasta:")
        if name:
            name = name.strip()
            if not name:
                messagebox.showwarning("Aviso", "Digite um nome válido!")
                return
            if name not in self.folders:
                self.folders[name] = []
                self.update_tree()
                self.save_data()
                self.update_status(f"📁 Pasta criada: {name}")
            else:
                messagebox.showwarning("Aviso", "Pasta já existe!")
    
    def create_playlist(self):
        if not self.folders:
            messagebox.showwarning("Aviso", "Crie uma pasta primeiro!")
            return
        
        folder_list = list(self.folders.keys())
        
        # Janela customizada para selecionar pasta
        dialog = tk.Toplevel(self.root)
        dialog.title("Nova Playlist")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        selected_folder = tk.StringVar(value=folder_list[0] if folder_list else "")
        playlist_name = tk.StringVar()
        
        ttk.Label(dialog, text="Selecione a pasta:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        folder_combo = ttk.Combobox(dialog, textvariable=selected_folder, values=folder_list, state='readonly', width=40)
        folder_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Nome da playlist:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        name_entry = ttk.Entry(dialog, textvariable=playlist_name, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        result = {'created': False, 'name': ''}
        
        def create():
            folder = selected_folder.get()
            name = playlist_name.get().strip()
            
            if not name:
                messagebox.showwarning("Aviso", "Digite um nome para a playlist!")
                return
            
            if folder and folder in self.folders:
                # Verifica se já existe playlist com esse nome na pasta
                existing_names = [p.name for p in self.folders[folder]]
                if name in existing_names:
                    messagebox.showwarning("Aviso", "Já existe uma playlist com esse nome nesta pasta!")
                    return
                
                playlist = Playlist(name)
                self.folders[folder].append(playlist)
                result['created'] = True
                result['name'] = name
                dialog.destroy()
        
        def on_enter(event):
            create()
        
        name_entry.bind('<Return>', on_enter)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Criar", command=create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self.root.wait_window(dialog)
        
        if result['created']:
            self.update_tree()
            self.save_data()
            self.update_status(f"🎵 Playlist criada: {result['name']}")
    
    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        for folder_name, playlists in self.folders.items():
            folder_id = self.tree.insert('', 'end', text=f"📁 {folder_name}", open=True)
            for playlist in playlists:
                duration = sum(1 for t in playlist.tracks)
                self.tree.insert(folder_id, 'end', text=f"🎵 {playlist.name} ({duration})", 
                               values=(folder_name, playlist.name))
    
    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            if item['values']:
                folder_name, playlist_name = item['values']
                for playlist in self.folders[folder_name]:
                    if playlist.name == playlist_name:
                        self.load_playlist(playlist)
                        break
    
    def on_track_double_click(self, event):
        self.play_track()
    
    def load_playlist(self, playlist: Playlist):
        self.current_playlist = playlist
        self.current_label.config(text=f"🎵 Playlist: {playlist.name}")
        self.tracks_list.delete(0, tk.END)
        for track in playlist.tracks:
            start_info = f" [⏱{track.start_time}s]" if track.start_time > 0 else ""
            self.tracks_list.insert(tk.END, f"{track.title}{start_info}")
        self.update_status(f"✅ Playlist '{playlist.name}' carregada com {len(playlist.tracks)} música(s)")
        
        if self.shuffle_mode:
            self.generate_shuffle_queue()
    
    def update_status(self, message: str):
        self.status_label.config(text=message)
    
    def format_duration(self, seconds: int) -> str:
        if seconds == 0 or seconds is None:
            return "?"
        try:
            seconds = int(seconds)  # Garante que é inteiro
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}:{secs:02d}"
        except:
            return "?"
    
    def save_data(self):
        try:
            data = {folder: [p.to_dict() for p in playlists] 
                    for folder, playlists in self.folders.items()}
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Dados salvos: {len(self.folders)} pastas")
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar dados:\n{str(e)}")
    
    def load_data(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.folders = {folder: [Playlist.from_dict(p) for p in playlists]
                              for folder, playlists in data.items()}
                print(f"Dados carregados: {len(self.folders)} pastas")
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                self.folders = {}

    def on_closing(self):
        """Salva dados antes de fechar"""
        try:
            self.save_data()
            self.player.stop()
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RPGSoundboard(root)
    root.mainloop()