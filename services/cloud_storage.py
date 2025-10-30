from google.cloud import storage
from config import settings
import os
import json

class CloudStorage:
    def __init__(self):
        if os.getenv("GOOGLE_CREDENTIALS_JSON"):
            creds_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
            self.client = storage.Client.from_service_account_info(creds_info)
        else:
            if os.path.exists(settings.GOOGLE_CREDENTIALS_PATH):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_CREDENTIALS_PATH
                self.client = storage.Client()
            else:
                raise RuntimeError(
                    "No se encontraron credenciales de Google. "
                    "Define GOOGLE_CREDENTIALS_JSON o coloca el archivo en la ruta especificada."
                )
        self.bucket = self.client.bucket(settings.GOOGLE_STORAGE_BUCKET)

    async def upload_file(self, file_path: str, destination_name: str) -> str:
        blob = self.bucket.blob(f"reports/{destination_name}")
        blob.upload_from_filename(file_path)
        blob.make_public() 
        return blob.public_url

    async def delete_file(self, file_path: str):
        blob = self.bucket.blob(file_path)
        blob.delete()

cloud_storage = CloudStorage()
