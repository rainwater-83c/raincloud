import moderngl
import sys

backends = ["egl", "wgl", "x11"]

for backend in backends:
    try:
        ctx = moderngl.create_standalone_context(backend=backend)
        print(f"SUCCESS: {backend}")
        print("OpenGL version:", ctx.info["GL_VERSION"])
        ctx.release()
        break
    except Exception as e:
        print(f"FAILED: {backend}: {e}")
else:
    print("No standalone OpenGL context could be created.")