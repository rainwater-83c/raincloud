import os
import shutil
from pathlib import Path
import subprocess
import stat

def remove_readonly(func, path, exc_info):
    """Clear the read-only bit and retry the deletion."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        # If it still fails, the file might be locked by another process
        raise
try:
    shutil.rmtree("./dist", onexc=remove_readonly)
except FileNotFoundError:
    pass
shutil.copytree('src', 'dist')
subprocess.run(["python", "-m", "compileall", "-b", "./dist"],check=True)
os.rename('dist/main.py', 'dist/main.tmp')
for file_path in Path("./dist").rglob("*.py"):
    if file_path.is_file():
        file_path.unlink()
os.rename('dist/main.tmp', 'dist/main.py')
os.remove('./dist/main.pyc')
shutil.make_archive(base_name="./dist/assets", format="zip", root_dir="./dist", base_dir="assets")
shutil.make_archive(base_name="./dist/scripts", format="zip", root_dir="./dist", base_dir="scripts")
shutil.rmtree("./dist/assets", onexc=remove_readonly)
shutil.rmtree("./dist/scripts", onexc=remove_readonly)
os.rename('./dist/assets.zip', './dist/assets.rca')
os.rename('./dist/scripts.zip', './dist/scripts.rcs')
subprocess.run(['python','-m','nuitka','--onefile','--windows-icon-from-ico=icon.ico','--onefile-tempdir-spec={CACHE_DIR}/Raincloud/engine','main.py'],check=True,cwd='./dist')
shutil.rmtree("./dist/main.build", onexc=remove_readonly)
shutil.rmtree("./dist/main.dist", onexc=remove_readonly)
shutil.rmtree("./dist/main.onefile-build", onexc=remove_readonly)
os.remove('./dist/icon.ico')
os.remove('./dist/main.py')