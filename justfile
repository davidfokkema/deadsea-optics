set windows-shell := ["cmd.exe", "/c"]

venv:
    uv sync

[working-directory: 'src/ocean_optics']
compile:
    uv run pyside6-uic main_window.ui --output ui_main_window.py

design:
    uv run designer src/ocean_optics/main_window.ui

format:
    uvx ruff format

fix:
    uvx ruff check --fix

typecheck:
    uv run mypy -p ocean_optics --strict

[working-directory: 'src/ocean_optics/resources']
make-icons:
    sh create_icons.sh
