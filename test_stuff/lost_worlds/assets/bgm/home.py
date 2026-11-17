from pathlib import Path
audio = texture = Path(__file__).with_name("home.wav").read_bytes()

loop = True