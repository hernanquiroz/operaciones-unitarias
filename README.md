# Operaciones Unitarias — Diseño con Streamlit

App web para el diseño y análisis de equipos de operaciones unitarias en
ingeniería química. Primer módulo: **intercambiadores de calor** con los
métodos LMTD (con factor de corrección F) y ε-NTU.

## Módulos

| Módulo | Métodos | Estado |
|---|---|---|
| Intercambiadores de calor | LMTD + F, ε-NTU, dimensionamiento y simulación (rating) | ✅ |
| Destilación (McCabe–Thiele) | — | 🚧 próximamente |
| Evaporación | — | 🚧 próximamente |

## Instalación y ejecución local

```bash
git clone https://github.com/TU_USUARIO/operaciones-unitarias.git
cd operaciones-unitarias
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

La app abre en `http://localhost:8501`.

## Despliegue en Streamlit Community Cloud

1. Sube este repo a GitHub (público).
2. Entra a [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Selecciona el repo, rama `main` y archivo `app.py` → **Deploy**.
4. Cada `git push` actualiza la app automáticamente.

## Configuraciones soportadas (ε-NTU)

- Contraflujo
- Flujo paralelo
- Carcasa y tubos 1-2 (1 paso por carcasa, 2 por tubos)
- Flujo cruzado, ambos fluidos sin mezclar
- Flujo cruzado, Cmax mezclado
- Flujo cruzado, Cmin mezclado

## Tests

```bash
pytest -q
```

## Referencias

- Incropera, F. P. et al., *Fundamentals of Heat and Mass Transfer*, 7.ª ed., Wiley.
- Shah, R. K. & Sekulic, D. P., *Fundamentals of Heat Exchanger Design*, Wiley.
