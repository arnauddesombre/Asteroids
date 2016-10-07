@echo off
python -O -OO asteroids.py --stop-timers

rem  Options:
rem  --stop-timers       : automatically stop timers when program is stopped
rem  --display-fps       : display frame per second rate on the canvas
rem  --no-controlpanel   : remove control panel from the left section
rem  --default-font      : utilise la police de caractère par défaut de Pygame 
rem  --print-load-medias : affiche dans la console les medias charges

pause