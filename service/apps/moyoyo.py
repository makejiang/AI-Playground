# filepath: c:\Users\asd\Source\AI-Playground\service\apps\moyoyo.py
import logging
from . import winutils
from .base_app import BaseApp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class app(BaseApp):
    def __init__(self):
        super().__init__()

    def is_running(self, process_name: str):
        count = winutils.appisrunning_count(process_name.split('\\')[-1])
        logger.info(f"Process '{process_name}' is running {count} times")
        if count > 5:
            return True
        else:
            self.close(process_name)
            return False


app_instance = app()
