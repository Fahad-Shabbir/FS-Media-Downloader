import os
import sys

# Prevent Windows GPU Watchdog / TDR timeouts in WebView2
curr_args = os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "")
safe_flags = "--disable-features=CalculateNativeWinOcclusion,ElasticOverscroll --disable-gpu-process-crash-limit"
os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"{safe_flags} {curr_args}".strip()

# Initialize yt-dlp update override BEFORE importing downloader or yt_dlp
import updater
updater.setup_ytdlp_override()

def main():
    """Main launcher: starts the Liquid Glass engine by default, or fallback if requested."""
    if "--classic" not in sys.argv:
        try:
            import app_glass
            app_glass.main()
            return
        except Exception as e:
            try:
                import traceback
                log_file = os.path.join(updater.get_local_appdata_dir(), "app.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[LiquidGlass Error] {e}\n")
                    traceback.print_exc(file=f)
            except Exception:
                pass

    try:
        import app_classic
        app_classic.main()
    except Exception as e:
        try:
            import traceback
            log_file = os.path.join(updater.get_local_appdata_dir(), "app.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[Fatal Error] {e}\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
