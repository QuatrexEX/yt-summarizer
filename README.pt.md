# YT Summarizer

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **[English](README.md)** | **[日本語](README.ja.md)** | **[한국어](README.ko.md)** | **[简体中文](README.zh-CN.md)** | **[Español](README.es.md)**

Um aplicativo de desktop que obtém transcrições de vídeos do YouTube e gera resumos com IA usando a API Gemini.

## Recursos

- **Obtenção de transcrições**: Recupera automaticamente transcrições de vídeos (suporte multilíngue)
- **Resumos com IA**: Gera resumos concisos usando Google Gemini 2.5 Flash
- **Suporte multilíngue**: Interface disponível em 6 idiomas (japonês, inglês, coreano, chinês, espanhol, português)
- **Gerenciamento de vídeos**: Salve e gerencie múltiplos vídeos com miniaturas
- **Renderização Markdown**: Resumos são exibidos com markdown formatado
- **Tamanho de fonte ajustável**: Ctrl+roda do mouse para zoom (50%-200%)

## Requisitos

- Python 3.10 ou superior
- Chave API Gemini ([Obter no Google AI Studio](https://aistudio.google.com/app/apikey))

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/QuatrexEX/yt-summarizer.git
cd yt-summarizer
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute o aplicativo:
```bash
python yt-summarizer.py
```

No Windows, você também pode clicar duas vezes em `yt-summarizer.bat`

## Uso

1. Clique no botão **Configurações** (canto superior direito) e insira sua chave API Gemini
2. Cole uma URL do YouTube no campo de entrada e clique em **+** para adicionar um vídeo
3. Selecione um vídeo da lista (a transcrição será obtida automaticamente)
4. Clique em **Gerar** para criar um resumo com IA
5. Clique em **Assistir no YouTube** para abrir o vídeo

## Estrutura do Projeto

```
yt-summarizer/
├── yt-summarizer.py       # Aplicativo principal
├── yt-summarizer.bat      # Inicializador Windows
├── app/
│   ├── constants.py       # Constantes do aplicativo
│   ├── models/            # Modelos de dados
│   │   └── video.py       # Classes Video, Store
│   ├── services/          # Lógica de negócio
│   │   ├── youtube.py     # Utilitários YouTube
│   │   ├── transcript.py  # Obtenção de transcrições
│   │   └── gemini.py      # Integração API Gemini
│   └── i18n/              # Internacionalização
│       ├── __init__.py    # I18nManager
│       └── locales/       # Arquivos de tradução
├── data/                  # Dados locais (gitignore)
│   ├── videos.json        # Lista de vídeos
│   ├── settings.json      # Configurações do usuário
│   └── summaries/         # Resumos gerados
└── requirements.txt
```

## Idiomas Suportados

| Idioma | Código |
|--------|--------|
| Japonês | ja |
| Inglês | en |
| Coreano | ko |
| Chinês (Simplificado) | zh-CN |
| Espanhol | es |
| Português | pt |

## Dependências

- `youtube-transcript-api` - Obtém transcrições do YouTube
- `google-generativeai` - Cliente API Google Gemini
- `Pillow` - Processamento de imagens para miniaturas
- `requests` - Requisições HTTP

## Licença

Licença MIT - veja [LICENSE](LICENSE) para detalhes.

## Contribuir

Contribuições são bem-vindas! Sinta-se à vontade para enviar um Pull Request.
