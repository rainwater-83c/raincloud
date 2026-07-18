@echo off
rmdir /s /q "dist"
robocopy "src" "dist" /E /COPY:DAT /R:2 /W:5
cd "dist"
call python3 -m compileall -b .
ren "main.py" "main.tmp"
del /s /q *.py
ren "main.tmp" "main.py"
del "main.pyc"
pause
powershell -Command "Compress-Archive -Path 'scripts' -DestinationPath 'scripts.zip' -Force"
powershell -Command "Compress-Archive -Path 'assets' -DestinationPath 'assets.zip' -Force"
rmdir /s /q "scripts"
rmdir /s /q "assets"
ren "scripts.zip" "scripts.rcs"
ren "assets.zip" "assets.rca"
call nuitka --onefile --windows-icon-from-ico=icon.ico --onefile-tempdir-spec="{CACHE_DIR}/Raincloud/engine" --windows-console-mode=disable main.py
rmdir /s /q "main.build"
rmdir /s /q "main.dist"
rmdir /s /q "main.onefile-build"
del "icon.ico"
del "main.py"
pause