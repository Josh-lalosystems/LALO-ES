from connectors.base_connector import BaseConnector

from O365 import Account

class SharePointConnector(BaseConnector):
    def __init__(self, config: dict):
        super().__init__(config)
        credentials = (config.get('client_id'), config.get('client_secret'))
        self.account = Account(credentials)
        if not self.account.is_authenticated:
            self.account.authenticate(scopes=['basic', 'sharepoint'])

    def connect(self):
        # Test authentication
        return self.test_connection()

    def test_connection(self):
        try:
            sharepoint = self.account.sharepoint()
            sites = list(sharepoint.get_sites())
            return True if sites else False
        except Exception:
            return False

    def sync(self):
        # Example: List documents in the first site
        try:
            sharepoint = self.account.sharepoint()
            sites = list(sharepoint.get_sites())
            if not sites:
                return []
            site = sites[0]
            drive = site.get_default_drive()
            items = list(drive.get_items())
            return [item.name for item in items]
        except Exception:
            return []
