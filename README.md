# 🎵 BellumBoard - RPG Soundboard

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**Uma ferramenta para mestres de RPG criarem e gerenciarem trilhas sonoras épicas para suas sessões!**

[Características](#-características) • [Instalação](#-instalação) • [Como Usar](#-como-usar) • [Capturas de Tela](#-capturas-de-tela) • [Contribuir](#-contribuir)

</div>

---

## 📖 Sobre o Projeto

**BellumBoard** é um soundboard intuitivo e poderoso desenvolvido especialmente para mestres de RPG que desejam adicionar uma camada imersiva de áudio às suas sessões. Com integração direta ao YouTube, você pode buscar, organizar e reproduzir músicas sem precisar sair da aplicação.

### 🎯 Por que usar o BellumBoard?

- **🎮 Foco em RPG**: Criado pensando nas necessidades específicas de mestres
- **🌐 YouTube Integration**: Acesso a milhões de músicas e efeitos sonoros
- **📁 Organização Inteligente**: Sistema de pastas e playlists para cada tipo de cena
- **⚡ Reprodução Instantânea**: Sem downloads, streaming direto
- **🎲 Modo Aleatório**: Mantenha a atmosfera sempre variada
- **⏱️ Tempo Customizável**: Comece as músicas exatamente onde você quer

---

## ✨ Características

### 🔍 Busca e Importação
- **Busca no YouTube**: Encontre qualquer música ou efeito sonoro
- **Adicionar por URL**: Cole links diretos do YouTube
- **Importar do Spotify**: Importe playlists inteiras do Spotify (busca automática no YouTube)

### 🎼 Gerenciamento de Playlists
- **Organização em Pastas**: Separe por campanha, tipo de cena ou tema
- **Múltiplas Playlists**: Crie quantas precisar
- **Reordenação**: Mova músicas para cima/baixo facilmente
- **Tempo de Início**: Defina onde cada música deve começar

### 🎛️ Controles de Reprodução
- **Player Integrado**: Reprodução direta sem abrir navegador
- **Controles Completos**: Play, Pause, Stop, Próxima
- **Modo Aleatório**: Reprodução shuffle
- **Auto-Play**: Toca a próxima música automaticamente
- **Controle de Volume**: Ajuste preciso com slider

### 💾 Persistência
- **Salvamento Automático**: Seus dados são salvos automaticamente
- **Formato JSON**: Fácil de fazer backup e editar manualmente se necessário

---

## 🚀 Instalação

### Pré-requisitos

1. **Python 3.8 ou superior**
   ```bash
   python --version
   ```

2. **VLC Media Player**
   - Windows/Mac: [Download VLC](https://www.videolan.org/vlc/)
   - Linux: `sudo apt install vlc`

### Instalação das Dependências

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/bellumboard.git
cd bellumboard

# Instale as dependências Python
pip install python-vlc yt-dlp requests
```

### Executando o Programa

```bash
python bellumboard.py
```

---

## 📚 Como Usar

### 1️⃣ Criar Estrutura Organizacional

1. **Criar Pasta**: `Arquivo → Nova Pasta`
   - Exemplo: "Dungeons", "Taverna", "Combate", "Ambiente"

2. **Criar Playlist**: `Arquivo → Nova Playlist`
   - Selecione a pasta desejada
   - Dê um nome descritivo (ex: "Batalha contra Dragão")

### 2️⃣ Adicionar Músicas

**Opção 1: Busca no YouTube**
```
1. Digite o termo de busca (ex: "epic battle music")
2. Clique em "🔍 Buscar"
3. Dê duplo clique no resultado desejado
```

**Opção 2: URL Direta**
```
1. Cole a URL do YouTube
2. Clique em "➕ Adicionar URL"
```

**Opção 3: Importar do Spotify**
```
1. Cole a URL da playlist do Spotify
2. Clique em "📋 Importar Playlist Spotify"
3. Aguarde a busca automática no YouTube
```

### 3️⃣ Reproduzir

1. **Selecione a playlist** na árvore à esquerda (duplo clique)
2. **Escolha a música** na lista
3. **Clique em ▶ Tocar** ou dê duplo clique na música

### 4️⃣ Recursos Avançados

**Definir Tempo de Início**
- Útil para pular intros longas
- Selecione a música → `⏱ Definir Início`
- Digite o tempo em segundos

**Reordenar Playlist**
- Use `⬆ Mover para Cima` e `⬇ Mover para Baixo`

**Modo Aleatório**
- Marque `🔀 Aleatório` para shuffle
- Ideal para músicas de ambiente

**Auto-Play**
- Marque `🔁 Auto-Play`
- As músicas tocam automaticamente uma após a outra

---

## 🖼️ Capturas de Tela

### Interface Principal
```
┌─────────────────────────────────────────────────────────────┐
│  📁 BellumBoard                    🔍 Adicionar Músicas      │
│  ├─ 📁 Dungeons                    ┌───────────────────────┐│
│  │  ├─ 🎵 Exploração (12)          │ Buscar: [_________]   ││
│  │  ├─ 🎵 Combate (8)              │ URL: [_____________]  ││
│  │  └─ 🎵 Boss Fight (5)           └───────────────────────┘│
│  ├─ 📁 Taverna                                               │
│  │  └─ 🎵 Ambiente (15)            Resultados:              │
│  └─ 📁 Viagem                       1. Epic Battle Music... │
│     └─ 🎵 Estrada (10)              2. Fantasy Tavern...    │
│                                      3. Dragon Boss...       │
│  🎵 Playlist Atual: Combate                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ • Dark Souls - Boss Theme                                ││
│  │ • Skyrim - Combat Music                                  ││
│  │ • The Witcher 3 - Steel for Humans [⏱30s]              ││
│  └─────────────────────────────────────────────────────────┘│
│  [▶ Tocar] [⏸ Pausar] [⏹ Parar] [⏭ Próxima]               │
│  [🔀 Aleatório] [🔁 Auto-Play]  🔊 Volume: [======] 70%    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**: Linguagem principal
- **Tkinter**: Interface gráfica nativa
- **python-vlc**: Reprodução de áudio
- **yt-dlp**: Extração de streams do YouTube
- **requests**: Importação de playlists do Spotify

---

## 📋 Estrutura de Arquivos

```
bellumboard/
├── bellumboard.py              # Arquivo principal
├── soundboard_data.json        # Dados salvos (gerado automaticamente)
├── requirements.txt            # Dependências Python
└── README.md                   # Este arquivo
```

### Formato do soundboard_data.json

```json
{
  "Dungeons": [
    {
      "name": "Combate",
      "tracks": [
        {
          "title": "Epic Battle Music",
          "url": "https://www.youtube.com/watch?v=...",
          "video_id": "...",
          "start_time": 0
        }
      ]
    }
  ]
}
```

---



## 🐛 Problemas Conhecidos

- **VLC não encontrado**: Certifique-se de que o VLC está instalado e no PATH do sistema
- **Importação do Spotify lenta**: A busca no YouTube é feita música por música (pode levar alguns minutos para playlists grandes)
- **Algumas músicas não tocam**: Vídeos com restrição geográfica ou removidos não funcionarão

---

## 📝 Roadmap

- [ ] Suporte a efeitos sonoros com atalhos de teclado
- [ ] Fade in/fade out automático
- [ ] Exportar/Importar playlists
- [ ] Integração com APIs de RPG (Roll20, Foundry VTT)
- [ ] Modo escuro
- [ ] Suporte a loop de músicas individuais
- [ ] Cache de streams para reprodução offline

---

## 📄 Licença

Este projeto está sob a licença MIT.

---

## 👨‍💻 Autor

**Vinícius Filgueiras**

- GitHub: [@ViniFilgueiras](https://github.com/ViniFilgueiras)

---

## 🙏 Agradecimentos

- Comunidade RPG pelo feedback e sugestões
- [VLC](https://www.videolan.org/) pela excelente biblioteca de mídia
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) pelo poderoso extrator do YouTube
- Todos os mestres que tornam as sessões memoráveis! 🎲

---

<div align="center">

**⭐ Se este projeto foi útil para você, considere dar uma estrela no GitHub! ⭐**

*Feito com ❤️ para mestres de RPG em todo o mundo*

</div>
