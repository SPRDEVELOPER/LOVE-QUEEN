import logging
import sys

from telegram import Update

from src.bot.app import build_application
from src.config.settings import load_settings


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        settings = load_settings()
    except RuntimeError as exc:
        sys.exit(f"Configuration error: {exc}")

    app = build_application(settings)
    if settings.mode == "webhook":
        app.run_webhook(
            listen="0.0.0.0",
            port=settings.port,
            url_path=settings.webhook_path,
            webhook_url=f"{settings.webhook_base}/{settings.webhook_path}",
            secret_token=settings.webhook_secret,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
    else:
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
