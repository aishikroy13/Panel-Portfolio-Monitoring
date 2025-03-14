#!/bin/bash
panel serve dashboard_panel.py --allow-websocket-origin="*" --port=${PORT:-5006}
