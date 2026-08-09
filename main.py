# -*- coding: utf-8 -*-
"""
main.py
Ponto de entrada do aplicativo Captura Link de Pagamento - Kroton.
"""

import logging
import sys

import config


def configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    configurar_logging()
    logger = logging.getLogger("main")
    logger.info("Iniciando %s v%s", config.NOME_APP, config.VERSAO_APP)

    from app_gui import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.getLogger("main").exception("Falha inesperada ao iniciar o aplicativo.")
        sys.exit(1)
