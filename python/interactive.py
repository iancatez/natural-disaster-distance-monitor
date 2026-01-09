#!/usr/bin/env python3
"""
Natural Disaster Distance Monitor - Interactive CLI

A beautiful, interactive command-line interface for monitoring
natural disasters near any location.

Run without arguments to start the interactive session:
    python interactive.py
"""

import re
import sys
import logging
from typing import List, Optional, Tuple

# Rich for beautiful terminal output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich import box

# Questionary for interactive prompts
import questionary
from questionary import Style as QStyle

from disasters import (
    get_nearby_disasters,
    DisasterType,
    LocationResults,
    configure_logging,
)

# Initialize Rich console
console = Console()

# Custom questionary style - cyberpunk/terminal aesthetic
PROMPT_STYLE = QStyle([
    ('qmark', 'fg:#ff6b6b bold'),        # Question mark
    ('question', 'fg:#4ecdc4 bold'),      # Question text
    ('answer', 'fg:#ffe66d bold'),        # User answer
    ('pointer', 'fg:#ff6b6b bold'),       # Selection pointer
    ('highlighted', 'fg:#1a1a2e bg:#ff6b6b bold'),  # Highlighted choice
    ('selected', 'fg:#95e1d3'),           # Selected items
    ('separator', 'fg:#6c757d'),          # Separator line
    ('instruction', 'fg:#6c757d'),        # Instructions
    ('text', 'fg:#f8f9fa'),               # Normal text
])

# Color palette
COLORS = {
    'title': '#ff6b6b',
    'subtitle': '#4ecdc4',
    'warning': '#ffe66d',
    'danger': '#ff6b6b',
    'success': '#95e1d3',
    'info': '#74b9ff',
    'muted': '#6c757d',
    'hurricane': '#ff6b6b',
    'tornado': '#ffe66d',
    'wildfire': '#ff9f43',
}

ASCII_BANNER = r"""
[#ff6b6b]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣦⣀⠀⠀⠀⠀⠀⠀⢲⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡆⠀⠀⠀⠀⠀⠀⠀⠛⣦⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣷⣤⠀⠀⠀⠀⠀⢻⣿⣷⣄⢀⠀⠀⠀⠀⠀⠀⢀⣴⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⣷⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣷⣄⠀⠀⠀⠀⣿⣿⣿⣷⠱⣆⠀⠀⠀⢀⣾⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣽⣿⡆⠀⠀⠀⢸⣿⣞⣿⣧⢸⣷⣤⠀⢸⣿⣯⣿⠆⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⡟⢰⣿⡷⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⣿⣦⡄⠀⠀⠀⠀⢻⣿⣶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣟⣾⣿⠀⠀⠀⣼⣿⡏⣿⣿⠀⣿⣿⣗⠺⣿⣳⣿⣧⠀⠀⠀⠀⠀⠀⠀⣴⣿⡟⠀⣸⣿⡟⣽⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣆⠀⠀⠀⠀⣿⣿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣦⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣯⢿⣿⡇⠀⣰⣿⡿⢸⣿⡿⠀⣼⣿⣻⡦⣿⣯⢿⣿⡆⠀⠀⠀⠀⢀⣾⣿⣿⠀⢠⣿⡿⢱⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⢯⣿⠀⠀⢠⠀⣼⣿⣻⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣷⡀⠀⠀⠀⠀⠀⣰⣿⣿⣞⣿⣿⠃⢀⣿⡿⣡⣿⡿⠃⢀⣿⣿⣽⣷⢹⣿⣻⢿⣿⡄⠀⠀⢀⣾⣿⢿⡇⠀⣾⣿⣱⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⠁⢀⡿⢰⣿⣣⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⡄⠀⠀⠀⢰⣿⣿⣻⣼⣿⡿⠀⢸⣿⢣⣿⡿⠁⣠⣿⣿⡟⣾⣿⢈⣿⣯⣟⣿⣷⠀⠀⣸⣿⣟⣿⡇⠀⣿⣧⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⣳⣿⡟⠀⣾⡇⢸⣷⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⡄⠀⢠⣿⣿⢯⣳⣿⣿⣦⣄⠘⣿⣿⡿⠁⣴⣿⣿⢯⣽⣿⡟⢀⣿⣷⢯⣿⣿⡇⠀⣿⣿⣽⣻⣿⠀⣿⣷⣿⠇⠀⠀⠀⠀⣀⠀⠀⢀⣼⣿⣿⣳⢿⣿⠁⣰⣿⣇⢸⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⣠⡾⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢠⣾⠇⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⢿⣷⠀⣿⣿⢯⣟⣼⣿⡇⢻⣿⣧⠘⣿⠃⣼⣿⡿⡽⣞⣿⣿⠁⢸⣿⣟⣮⢿⣿⡇⠀⣿⣿⢶⣻⣿⣇⠘⣿⣿⠀⠀⢀⣴⡿⠁⠀⣠⣿⢱⣿⣯⣽⣻⣿⠀⣿⡿⣿⡄⢻⣧⠀⠀⠀⠀⠀⠀⣴⣾⡟⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣰⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⢿⡇⢰⣿⣯⡟⣼⣿⣿⠁⠘⣿⣽⣧⠈⢰⣿⣯⡷⣛⣿⣿⠃⠀⣼⣿⣿⢼⣻⣿⡇⠀⢺⣿⡿⣼⣻⣿⣦⠘⠇⠀⣠⣿⡿⠁⠀⣰⣿⡟⢸⣿⣳⢾⡽⣿⣇⢸⣿⡿⣿⣆⠙⠀⠀⠀⠀⢀⣾⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢀⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⡿⣿⠃⣿⣟⣾⢡⡿⣿⡟⠀⠀⢿⣯⢿⡇⣼⣿⣞⡇⣿⣿⣯⠀⣼⣿⣿⠏⣾⣿⣟⣰⡇⠘⣿⣿⣳⣭⢿⣿⣧⠀⢠⣿⣿⡃⠀⢰⣿⡿⡇⠸⣿⣯⡇⢻⣿⣿⣯⣿⣿⣿⣿⣷⡀⠀⠀⢀⣿⣿⣻⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠐⣿⣯⣿⣇⠱⣆⡀⠀⠀⠀⣸⣿⡿⣽⡿⢸⣿⢯⡇⢸⣟⣯⣟⠀⠀⣻⣿⣻⣿⢼⣷⣻⠄⢸⣿⣿⣿⣿⡿⠏⣸⣿⣿⣷⣿⡅⠀⢸⣿⣷⣏⣾⣻⣿⡆⢸⣿⢿⡅⠀⣾⣿⣻⣿⠐⣿⣿⣻⡄⠻⣽⣿⣯⣿⣷⣻⢿⣿⡆⠀⢸⣿⣟⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠈⣧⡀⠀⢻⣿⣾⣿⣆⠹⣿⣆⠀⢠⣿⣿⡽⣿⡇⢸⣿⢯⡇⢸⣯⢿⣿⡀⣠⣿⣟⡷⣿⢸⣿⡽⣇⠀⡹⠾⠟⠋⢀⣾⣿⣿⣻⣿⢿⡆⠀⢈⣿⣿⢾⡘⣷⣻⣷⣸⣿⢿⣧⠀⣿⣿⣽⣿⡆⠘⣿⣿⣽⡀⢹⡾⣿⣯⢻⣿⣯⢿⣿⡄⢸⣿⣯⢿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣿⣷⡀⠸⣿⣷⣻⣿⡀⣿⣿⡧⢼⣿⢷⣻⣿⡇⢹⣿⣟⡆⠈⣿⣻⢿⣷⣿⡿⣭⣿⡟⠘⣿⣟⣯⠀⠐⡀⢂⢠⣿⣿⣿⠍⣿⣿⢿⣿⣦⣼⣿⣟⣾⠇⢹⣯⢿⡏⣿⡿⣿⡀⢺⣿⣞⣿⣿⣦⣹⣿⣯⠇⠀⣿⣻⣿⠀⣿⣯⣟⣿⣷⠈⣿⣿⢯⡿⣿⣧⡀⠀⠀⠀⢀⣀⣤
⠀⠀⠀⣿⣿⣇⠀⣿⣷⣻⣿⡇⢹⣯⣿⣼⣿⡇⣿⣿⡇⠘⣿⣯⡗⠀⢜⢯⡿⡽⣯⢷⣯⣿⡷⢨⣿⣟⣾⠀⡼⠁⡌⣾⣿⣿⡏⠀⣿⣿⢯⡿⣿⣟⣿⡽⣾⠀⠐⣯⣿⣟⢿⣿⢿⣷⡜⣿⣯⠺⣟⡿⣿⣟⡿⡀⠀⡿⣽⣿⠀⣿⣿⢞⣿⡟⣲⡿⢻⣿⣳⢟⣿⣿⡄⠀⣴⣿⣿⠃
⠀⠀⣼⣿⣯⡇⣼⣿⢷⣻⣿⠀⣽⡿⣽⣿⣿⣽⢸⣿⣿⣤⣿⣯⡟⢧⠈⢢⡙⡿⠁⣾⢿⣿⡇⢸⣿⣟⣾⠰⡇⣸⠱⣟⣿⣷⡀⠀⣿⣿⣳⢻⡽⣿⡳⣽⢣⠇⢈⡷⣿⣏⠸⣿⣯⢿⣿⡹⣿⣷⡈⠙⠳⠟⠐⠀⠀⣿⣿⣇⣼⣿⣯⢿⣿⣷⣿⡇⠘⣿⣯⡛⣾⣿⣟⢰⣿⢿⡟⠀
⠀⣼⣿⣿⣿⣽⣿⡿⣫⣿⡇⢰⣿⣟⣿⡏⣿⣿⣆⠹⢿⡿⣟⣷⡻⢸⡄⠀⢻⠃⠀⣿⣿⣿⣀⣾⣿⣽⡎⢸⠁⡏⠀⣿⣻⣿⣿⣾⣿⡿⣽⠃⢻⡷⣽⢋⡎⠀⣴⡿⣿⡿⢀⣿⣟⢺⣿⣧⠹⣿⣿⣄⠀⠙⡆⠀⠀⣿⣿⣿⣿⡟⣾⣿⣿⣿⡽⣇⠀⣹⣿⣽⠸⣿⣿⢨⣿⣿⣷⠀
⣼⣿⣟⣿⣿⣿⣿⢃⣿⣿⣷⣿⣿⢞⣿⡇⢸⣿⣽⡄⠠⡙⢿⣯⡗⢨⠀⠀⡘⠰⡰⠘⣿⢿⣿⢿⣻⡞⠁⡾⠀⢱⡐⠈⠷⣯⣟⣯⣟⡽⢏⠀⢨⡿⢁⡞⠀⢰⣿⣿⣿⠃⢈⣿⣿⡃⣿⣿⠄⢻⣿⣽⠀⠀⢧⡀⡆⢹⣾⡽⠃⣾⣿⡿⢸⣿⣽⣿⣦⣿⣿⡏⢘⣷⣿⢸⣿⢿⣿⡄
⣿⣿⢽⣿⣿⣿⢾⠀⢿⣻⢿⣯⠏⣾⣿⡇⠘⣿⣯⢿⠀⠙⣆⠹⠇⣤⠇⡄⡃⠀⡇⠀⢈⠙⠙⢋⡁⠀⠠⢹⠀⣄⠑⡌⠀⡀⠉⡈⢀⣰⡾⠀⣼⣣⠋⠇⡀⢺⣯⣿⡟⠀⢀⣿⣟⡇⣿⣿⡇⢸⣿⣾⠁⡆⢸⡇⢸⠈⡻⠀⢸⣟⣿⡇⠸⣿⣷⠻⣿⣿⠟⠀⣸⣿⣿⣾⣿⢯⣿⡧
⣿⣿⢸⣿⣿⣿⣻⡇⠈⠻⣿⠁⠨⡷⣿⣷⣤⣽⣿⣻⠅⠀⠘⡆⣸⠏⡰⠀⡇⡄⠘⡄⠂⠈⢀⠀⠲⣀⠀⣽⠀⡈⡦⡈⠢⢑⠀⣴⠞⢁⡠⢀⡽⠁⢸⠀⠀⢹⣿⣿⡇⢀⣾⣿⣿⠁⢿⣽⣿⣿⣿⠟⢠⠃⡘⢧⠈⢫⠀⠀⠸⣯⣿⣷⣤⣿⣿⡇⠘⣋⠆⢠⣿⣿⣿⣿⠏⣾⣿⡇
⠹⣿⣧⠻⣿⢿⣷⣻⣄⠘⣄⠀⢀⠿⣽⣻⢿⡿⣯⠟⠀⠀⠀⡼⠃⣴⠇⣸⠁⢸⢂⠘⢔⠀⡀⠀⡄⠻⣄⠘⣇⢡⠀⡉⠢⡀⠉⠁⡔⠋⠁⠨⠁⢀⢾⡀⠆⠘⣷⢿⣿⣿⣿⡿⠃⠀⢊⢉⡛⠋⠁⡠⠃⢠⠃⡘⠠⡀⢷⡀⡀⠻⢽⣿⣿⣿⠟⠀⠐⠁⣠⠿⠿⠛⠋⢁⣰⣿⣿⠁
⠀⠹⣿⣷⣌⡙⠛⠽⠷⢧⡈⠢⣄⠲⢍⡛⠳⠛⠁⢊⣠⠞⠋⣰⡟⢁⣴⠇⢀⠂⣦⣉⠢⢄⡑⠄⠈⣶⢄⣁⠙⠤⡂⠹⢦⣈⠓⠈⢠⡶⣼⡄⡶⣹⣧⣳⡘⠰⢌⡛⠚⢓⢫⠴⠁⠀⠈⠁⠀⢐⡭⠔⢒⡇⢠⣇⢠⣆⠈⣷⣈⠢⢄⡠⢉⠀⠀⣀⠄⠘⠁⠀⠀⣠⣴⡿⣿⡿⠋⠀
⠀⠀⠈⠙⠿⢽⣷⣶⣤⣤⣌⣦⣈⣳⣶⣤⣤⣴⣠⣭⣴⣶⣛⣧⣴⣾⣩⣴⣾⣧⣝⣯⣷⣶⣭⣗⣤⣈⣛⣶⣭⣝⣃⣂⣀⣉⣻⣦⣔⣿⣮⣅⣁⣻⣾⣽⣻⣧⣤⣥⣤⣠⣄⣤⣠⣤⣤⣴⣶⣯⣤⣶⣯⣴⣟⣿⣮⣟⣷⣮⣟⣿⣶⣶⣖⣶⣾⣥⣖⣶⣲⣮⣷⠿⠞⠋⠁⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠁⠀⠁⠀⠀⠀⠀⠀⠁⠀⠀⠀⠁⠀⠀⠀⠁⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠁⠈⠀⠀⠀⠁⠈⠀⠁⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]

[#74b9ff]  ▄▄▄▄▄▄                                          ▄▄▄     ▄▄▄                                             
 █▀██▀▀██                       █▄                 ███▄ ▄███                  █▄                          
   ██   ██ ▀▀                  ▄██▄      ▄         ██ ▀█▀ ██         ▄     ▀▀▄██▄      ▄    ▀▀ ▄        ▄▄
   ██   ██ ██ ▄██▀█ ▄▀▀█▄ ▄██▀█ ██ ▄█▀█▄ ████▄     ██     ██   ▄███▄ ████▄ ██ ██ ▄███▄ ████▄██ ████▄ ▄████
 ▄ ██   ██ ██ ▀███▄ ▄█▀██ ▀███▄ ██ ██▄█▀ ██        ██     ██   ██ ██ ██ ██ ██ ██ ██ ██ ██   ██ ██ ██ ██ ██
 ▀██▀███▀ ▄███▄▄██▀▄▀█▄███▄▄██▀▄██▄▀█▄▄▄▄█▀      ▀██▀     ▀██▄▄▀███▀▄██ ▀█▄██▄██▄▀███▀▄█▀  ▄██▄██ ▀█▄▀████
                                                                                                        ██
                                                                                                      ▀▀▀[/] 

        [#6c757d]----------------------------------------------------------------------------------------[/]
                        [#74b9ff]HURRICANES[/]            [#ffe66d]TORNADOES[/]            [#ff6b6b]WILDFIRES[/]
        [#6c757d]----------------------------------------------------------------------------------------[/]
"""


def show_banner():
    """Display the ASCII art banner."""
    console.print(ASCII_BANNER)


def validate_coordinate_format(text: str) -> Tuple[bool, Optional[float], Optional[float]]:
    """
    Validate and parse coordinate input.
    
    Accepts formats:
    - "lat, lon" (e.g., "29.7604, -95.3698")
    - "lat lon" (e.g., "29.7604 -95.3698")
    
    Returns:
        Tuple of (is_valid, latitude, longitude)
    """
    if not text or not text.strip():
        return False, None, None
    
    # Clean the input
    text = text.strip()
    
    # Try comma-separated format
    pattern = r'^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$'
    match = re.match(pattern, text)
    
    if not match:
        # Try space-separated format
        pattern = r'^(-?\d+\.?\d*)\s+(-?\d+\.?\d*)$'
        match = re.match(pattern, text)
    
    if not match:
        return False, None, None
    
    try:
        lat = float(match.group(1))
        lon = float(match.group(2))
        
        # Validate ranges
        if not (-90 <= lat <= 90):
            return False, None, None
        if not (-180 <= lon <= 180):
            return False, None, None
        
        return True, lat, lon
        
    except ValueError:
        return False, None, None


def get_coordinates() -> Tuple[float, float, str]:
    """
    Prompt user for coordinates with validation.
    
    Returns:
        Tuple of (latitude, longitude, location_name)
    """
    console.print()
    console.print("[#4ecdc4]📍 Enter Location Coordinates[/]", style="bold")
    console.print("[#6c757d]   Format: latitude, longitude (e.g., 29.7604, -95.3698)[/]")
    console.print()
    
    while True:
        coords = questionary.text(
            "Coordinates:",
            style=PROMPT_STYLE,
            validate=lambda x: validate_coordinate_format(x)[0] or "Invalid format. Use: lat, lon (e.g., 29.7604, -95.3698)"
        ).ask()
        
        if coords is None:  # User pressed Ctrl+C
            raise KeyboardInterrupt()
        
        is_valid, lat, lon = validate_coordinate_format(coords)
        
        if is_valid:
            break
    
    # Ask for optional location name
    name = questionary.text(
        "Location name (optional):",
        default="My Location",
        style=PROMPT_STYLE
    ).ask()
    
    if name is None:
        raise KeyboardInterrupt()
    
    return lat, lon, name or "My Location"


def get_disaster_types() -> List[DisasterType]:
    """
    Prompt user to select disaster types to query.
    
    Returns:
        List of selected DisasterType enums
    """
    console.print()
    
    choices = questionary.checkbox(
        "Select disaster types to monitor:",
        choices=[
            questionary.Choice("🌀 Hurricanes", value=DisasterType.HURRICANE, checked=True),
            questionary.Choice("🌪️  Tornadoes", value=DisasterType.TORNADO, checked=True),
            questionary.Choice("🔥 Wildfires", value=DisasterType.WILDFIRE, checked=True),
        ],
        style=PROMPT_STYLE,
        instruction="(Use arrow keys, space to select, enter to confirm)"
    ).ask()
    
    if choices is None:
        raise KeyboardInterrupt()
    
    if not choices:
        # Default to all if none selected
        return list(DisasterType)
    
    return choices


def get_radius() -> float:
    """
    Prompt user to select search radius.
    
    Returns:
        Radius in miles
    """
    console.print()
    
    choices = [
        questionary.Choice("25 miles", value=25.0),
        questionary.Choice("50 miles", value=50.0),
        questionary.Choice("100 miles (recommended)", value=100.0),
        questionary.Choice("150 miles", value=150.0),
        questionary.Choice("200 miles", value=200.0),
        questionary.Choice("Custom...", value=-1.0),
    ]
    
    radius = questionary.select(
        "Select search radius:",
        choices=choices,
        default=choices[2],  # 100 miles
        style=PROMPT_STYLE,
        instruction="(Use arrow keys)"
    ).ask()
    
    if radius is None:
        raise KeyboardInterrupt()
    
    if radius == -1.0:
        custom = questionary.text(
            "Enter custom radius (miles):",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Enter a positive number",
            style=PROMPT_STYLE
        ).ask()
        
        if custom is None:
            raise KeyboardInterrupt()
        
        return float(custom)
    
    return radius


def display_results(results: LocationResults):
    """Display query results with rich formatting."""
    console.print()
    
    # Header panel
    header = Table.grid(padding=1)
    header.add_column(justify="center")
    header.add_row(f"[bold #4ecdc4]📍 {results.location.name}[/]")
    header.add_row(f"[#6c757d]({results.location.latitude}, {results.location.longitude})[/]")
    header.add_row(f"[#6c757d]Search radius: {results.radius_miles} miles[/]")
    
    console.print(Panel(header, border_style="#4ecdc4", box=box.DOUBLE))
    
    # Hurricanes
    if results.hurricanes:
        console.print()
        console.print(f"[bold #ff6b6b]🌀 HURRICANES ({len(results.hurricanes)} found)[/]")
        
        table = Table(box=box.ROUNDED, border_style="#ff6b6b", show_header=True)
        table.add_column("Name", style="#ff6b6b bold")
        table.add_column("Distance", justify="right")
        table.add_column("Category", justify="center")
        table.add_column("Wind", justify="right")
        table.add_column("Status")
        
        for h in results.hurricanes:
            status = "[bold #ffe66d]⚠️ INSIDE CONE[/]" if h.inside_cone else ""
            dist = f"{h.distance_miles:.1f} mi"
            wind = f"{h.max_wind_mph:.0f} mph" if h.max_wind_mph else "N/A"
            table.add_row(h.name, dist, h.severity, wind, status)
        
        console.print(table)
    else:
        console.print()
        console.print("[#6c757d]🌀 No hurricanes within search radius[/]")
    
    # Tornadoes
    if results.tornadoes:
        console.print()
        console.print(f"[bold #ffe66d]🌪️  TORNADOES ({len(results.tornadoes)} found)[/]")
        
        table = Table(box=box.ROUNDED, border_style="#ffe66d", show_header=True)
        table.add_column("Rating", style="#ffe66d bold", justify="center")
        table.add_column("Distance", justify="right")
        table.add_column("Date")
        table.add_column("Path")
        table.add_column("Casualties", justify="center")
        
        for t in results.tornadoes:
            ef_str = f"EF{t.ef_scale.value}" if t.ef_scale else "?"
            dist = f"{t.distance_miles:.1f} mi"
            date = t.storm_date.strftime("%Y-%m-%d") if t.storm_date else "Unknown"
            path = f"{t.path_length_miles:.1f}mi × {t.path_width_yards:.0f}yd" if t.path_length_miles and t.path_width_yards else "N/A"
            
            casualties_parts = []
            if t.fatalities:
                casualties_parts.append(f"💀 {t.fatalities}")
            if t.injuries:
                casualties_parts.append(f"🤕 {t.injuries}")
            casualties = " ".join(casualties_parts) if casualties_parts else "-"
            
            table.add_row(ef_str, dist, date, path, casualties)
        
        console.print(table)
    else:
        console.print()
        console.print("[#6c757d]🌪️  No recent tornadoes within search radius[/]")
    
    # Wildfires
    if results.wildfires:
        console.print()
        console.print(f"[bold #ff9f43]🔥 WILDFIRES ({len(results.wildfires)} found)[/]")
        
        table = Table(box=box.ROUNDED, border_style="#ff9f43", show_header=True)
        table.add_column("Name", style="#ff9f43 bold")
        table.add_column("Distance", justify="right")
        table.add_column("Size", justify="right")
        table.add_column("Contained", justify="center")
        table.add_column("Status")
        
        for w in results.wildfires:
            status = "[bold #ff6b6b]🚨 INSIDE PERIMETER[/]" if w.inside_perimeter else ""
            dist = f"{w.distance_miles:.1f} mi"
            size = f"{w.acres:,.0f} ac" if w.acres else "Unknown"
            contained = f"{w.containment_percent:.0f}%" if w.containment_percent is not None else "?"
            table.add_row(w.name, dist, size, contained, status)
        
        console.print(table)
    else:
        console.print()
        console.print("[#6c757d]🔥 No active wildfires within search radius[/]")
    
    # Summary
    console.print()
    total = results.total_disasters
    if total > 0:
        style = "#ff6b6b bold" if total >= 5 else "#ffe66d bold" if total >= 2 else "#95e1d3 bold"
        console.print(Panel(
            f"[{style}]⚡ {total} TOTAL DISASTERS WITHIN {results.radius_miles} MILES[/]",
            border_style=style,
            box=box.DOUBLE
        ))
    else:
        console.print(Panel(
            "[#95e1d3 bold]✅ NO DISASTERS WITHIN SEARCH RADIUS[/]",
            border_style="#95e1d3",
            box=box.DOUBLE
        ))


def ask_continue() -> bool:
    """Ask if user wants to perform another query."""
    console.print()
    
    choice = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("🔍 Search another location", value="again"),
            questionary.Choice("👋 Exit", value="exit"),
        ],
        style=PROMPT_STYLE
    ).ask()
    
    return choice == "again"


def run_query(lat: float, lon: float, name: str, radius: float, types: List[DisasterType]) -> LocationResults:
    """Execute the disaster query with a loading spinner."""
    with Progress(
        SpinnerColumn(style="#4ecdc4"),
        TextColumn("[#4ecdc4]{task.description}[/]"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Scanning for nearby disasters...", total=None)
        
        results = get_nearby_disasters(
            latitude=lat,
            longitude=lon,
            radius_miles=radius,
            disaster_types=types,
            name=name
        )
        
        progress.update(task, description="Complete!")
    
    return results


def interactive_session():
    """Run the main interactive session loop."""
    # Suppress logging during interactive mode
    configure_logging(logging.WARNING)
    
    # Clear screen and show banner
    console.clear()
    show_banner()
    
    console.print()
    console.print("[#4ecdc4]Welcome to the Natural Disaster Distance Monitor![/]")
    console.print("[#6c757d]Track hurricanes, tornadoes, and wildfires near any location.[/]")
    
    try:
        while True:
            # Get user inputs
            lat, lon, name = get_coordinates()
            types = get_disaster_types()
            radius = get_radius()
            
            # Run query
            console.print()
            results = run_query(lat, lon, name, radius, types)
            
            # Display results
            display_results(results)
            
            # Ask to continue
            if not ask_continue():
                break
            
            console.print()
            console.print("[#6c757d]─" * 65 + "[/]")
    
    except KeyboardInterrupt:
        pass
    
    # Goodbye message
    console.print()
    console.print(Panel(
        "[#4ecdc4]Thanks for using Disaster Monitor! Stay safe! 🛡️[/]",
        border_style="#4ecdc4",
        box=box.ROUNDED
    ))
    console.print()


def main():
    """Main entry point."""
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    try:
        interactive_session()
    except Exception as e:
        console.print(f"[#ff6b6b]Error: {e}[/]")
        sys.exit(1)


if __name__ == '__main__':
    main()

