set windows-shell := ["cmd.exe", "/c"]

venv:
    uv sync

[working-directory: 'src/deadsea_optics']
compile:
    uv run pyside6-uic main_window.ui --output ui_main_window.py

design:
    uv run pyside6-designer src/deadsea_optics/main_window.ui

format:
    uvx ruff format

fix:
    uvx ruff check --fix

typecheck:
    uv run mypy -p deadsea_optics --strict

[working-directory: 'src/deadsea_optics/resources']
make-icons:
    sh create_icons.sh
