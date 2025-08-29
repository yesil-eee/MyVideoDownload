try:
    # Frozen/packaged absolute import
    from myvideodownload.ui import run_app  # type: ignore
except Exception:
    # Dev mode fallback when running as a module
    from .ui import run_app

if __name__ == "__main__":
    raise SystemExit(run_app())
