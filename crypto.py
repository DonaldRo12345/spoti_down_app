class SimpleEncryption:

    """encrypt and decrypt an uri"""

    def __init__(self, url: str, key: str = "loremipsum"):
        self.url = url
        self.key = key

    def _encrypt_url(self):
        self.key = self.key.ljust(len(self.url), "X")
        encrypted_url = ""
        for i in range(len(self.url)):
            encrypted_url += chr(ord(self.url[i]) ^ ord(self.key[i]))
        return encrypted_url

    def _decrypt_url(self, encrypted_url):
        self.key = self.key.ljust(len(encrypted_url), "X")
        url = ""
        for i in range(len(encrypted_url)):
            url += chr(ord(encrypted_url[i]) ^ ord(self.key[i]))
        return url
