# YT Summarizer

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **[English](README.md)** | **[日本語](README.ja.md)** | **[한국어](README.ko.md)** | **[简体中文](README.zh-CN.md)** | **[Português](README.pt.md)**

Una aplicación de escritorio que obtiene transcripciones de videos de YouTube y genera resúmenes con IA usando la API de Gemini.

## Características

- **Obtención de transcripciones**: Recupera automáticamente las transcripciones de videos (soporte multiidioma)
- **Resúmenes con IA**: Genera resúmenes concisos usando Google Gemini 2.5 Flash
- **Soporte multiidioma**: Interfaz disponible en 6 idiomas (japonés, inglés, coreano, chino, español, portugués)
- **Gestión de videos**: Guarda y administra múltiples videos con miniaturas
- **Renderizado Markdown**: Los resúmenes se muestran con formato markdown
- **Tamaño de fuente ajustable**: Ctrl+rueda del ratón para zoom (50%-200%)

## Requisitos

- Python 3.10 o superior
- Clave API de Gemini ([Obtener en Google AI Studio](https://aistudio.google.com/app/apikey))

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/QuatrexEX/yt-summarizer.git
cd yt-summarizer
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
python yt-summarizer.py
```

En Windows, también puedes hacer doble clic en `yt-summarizer.bat`

## Uso

1. Haz clic en el botón **Configuración** (arriba a la derecha) e ingresa tu clave API de Gemini
2. Pega una URL de YouTube en el campo de entrada y haz clic en **+** para agregar un video
3. Selecciona un video de la lista (la transcripción se obtendrá automáticamente)
4. Haz clic en **Generar** para crear un resumen con IA
5. Haz clic en **Ver en YouTube** para abrir el video

## Estructura del Proyecto

```
yt-summarizer/
├── yt-summarizer.py       # Aplicación principal
├── yt-summarizer.bat      # Lanzador de Windows
├── app/
│   ├── constants.py       # Constantes de la aplicación
│   ├── models/            # Modelos de datos
│   │   └── video.py       # Clases Video, Store
│   ├── services/          # Lógica de negocio
│   │   ├── youtube.py     # Utilidades de YouTube
│   │   ├── transcript.py  # Obtención de transcripciones
│   │   └── gemini.py      # Integración API Gemini
│   └── i18n/              # Internacionalización
│       ├── __init__.py    # I18nManager
│       └── locales/       # Archivos de traducción
├── data/                  # Datos locales (gitignore)
│   ├── videos.json        # Lista de videos
│   ├── settings.json      # Configuración del usuario
│   └── summaries/         # Resúmenes generados
└── requirements.txt
```

## Idiomas Soportados

| Idioma | Código |
|--------|--------|
| Japonés | ja |
| Inglés | en |
| Coreano | ko |
| Chino (Simplificado) | zh-CN |
| Español | es |
| Portugués | pt |

## Dependencias

- `youtube-transcript-api` - Obtiene transcripciones de YouTube
- `google-generativeai` - Cliente API de Google Gemini
- `Pillow` - Procesamiento de imágenes para miniaturas
- `requests` - Solicitudes HTTP

## Licencia

Licencia MIT - ver [LICENSE](LICENSE) para más detalles.

## Contribuir

¡Las contribuciones son bienvenidas! No dudes en enviar un Pull Request.
