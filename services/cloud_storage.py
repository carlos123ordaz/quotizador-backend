from datetime import datetime, timedelta, timezone
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
from config import settings
import os

class CloudStorage:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        self.container_name = settings.AZURE_STORAGE_CONTAINER
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
        self.account_key = self._extract_account_key()
        # Ensure the container exists
        container_client = self.blob_service_client.get_container_client(self.container_name)
        try:
            container_client.get_container_properties()
        except Exception:
            container_client.create_container()

    def _extract_account_key(self) -> str:
        for part in self.connection_string.split(";"):
            if part.startswith("AccountKey="):
                return part[len("AccountKey="):]
        return ""

    def _generate_sas_url(self, blob_name: str) -> str:
        sas_token = generate_blob_sas(
            account_name=self.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(days=30),
        )
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

    async def upload_file(self, file_path: str, destination_name: str) -> str:
        blob_name = f"reports/{destination_name}"
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        with open(file_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            )
        return self._generate_sas_url(blob_name)

    async def delete_file(self, file_path: str):
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path
        )
        blob_client.delete_blob()

cloud_storage = CloudStorage()
