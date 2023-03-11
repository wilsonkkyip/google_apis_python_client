import requests 
import jwt 
from time import time
import os 
import json


def oauth_refresh(acc_secret):
    """
    Refresh client token for Google API

    Parameters
    ----------
    acc_secret: str / dict
        Can be one of the following:
            - developer key (or api key)
            - path to `service_account.json` (service account)
                    or `client_token.json`  (client oauth)
            - JSON content of the above files

    Reference
    ---------
    https://developers.google.com/identity/protocols/oauth2/web-server
    """
    url = acc_secret.get("token_uri", "https://oauth2.googleapis.com/token")
    body = {
        "client_id": acc_secret["client_id"],
        "client_secret": acc_secret["client_secret"],
        "refresh_token": acc_secret["refresh_token"],
        "grant_type": "refresh_token"
    }
    res = requests.post(url, json=body)
    if not res.ok:
        print(json.dumps(res.json(), indent=4))
        res.raise_for_status()
    return res.json()


def oauth_service(acc_secret, scopes):
    """
    Refresh service account token for Google API

    Parameters
    ----------
    acc_secret: str / dict
        Can be one of the following:
            - developer key (or api key)
            - path to `service_account.json` (service account)
                    or `client_token.json`  (client oauth)
            - JSON content of the above files

    Reference
    ---------
    https://developers.google.com/identity/protocols/oauth2/service-account
    """
    if type(scopes) is list:
        scopes = " ".join(scopes)

    url = acc_secret.get("token_uri", "https://oauth2.googleapis.com/token")

    payload = {
        "iss": acc_secret["client_email"],
        "scope": scopes,
        "aud": url,
        "iat": time(),
        "exp": time() + 3600
    }

    headers = {'kid': acc_secret["private_key_id"]}

    signed_jwt = jwt.encode(
        payload, acc_secret["private_key"], headers=headers, algorithm='RS256'
    )

    body = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": signed_jwt
    }
    
    res = requests.post(url, json=body)
    if not res.ok:
        print(json.dumps(res.json(), indent=4))
        res.raise_for_status()
    return res.json()


class Credential:
    """
    A class storing a Google auth credential

    Parameters
    ----------
    acc_secret: str / dict
        Can be one of the following:
            - developer key (or api key)
            - path to `service_account.json` (service account)
                    or `client_token.json`  (client oauth)
            - JSON dict of the above files
    
    Methods
    -------
    refresh - refreshing the authentication token

    Attributes
    ----------
    token:             The authenticated token
    token_type:        The token type to put in `Authorization` in headers
    headers:           The authenticated http headers
    oauth_response:    The response from OAuth token request
    cred_type:         One of `api_key`, `service_account` or `client_id`
    expriy:            Expiry timestamp
    scopes:            A list of authorized scopes
    """
    def __init__(self, acc_secret):
        if type(acc_secret) is str:
            if os.path.isfile(acc_secret):
                with open(acc_secret, "r") as f:
                    acc_secret = json.load(f)

        self._acc_secret = acc_secret
        self._expiry = time()
        if "client_email" in acc_secret:
            self._cred_type = "service_account"
            self._scopes = [
                # Full control on Google Drive, Sheets, Slides, Docs and Apps Script
                "https://www.googleapis.com/auth/drive",
                # Full control on YouTube account
                "https://www.googleapis.com/auth/youtube",
                # Full control on Google Mail
                "https://mail.google.com/"
            ]
        elif "refresh_token" in acc_secret:
            self._cred_type = "client_id"
        else:
            self._cred_type = "api_key"
            self._scopes = []
            self._oauth_response = {"access_token": acc_secret}
            self._expiry = time() + time()
        
        self.refresh()

    def refresh(self):
        """
        Refresh the token when expired and create the headers for API requests
        """
        if time() > self._expiry :
            if self._cred_type == "service_account":
                self._oauth_response = oauth_service(self._acc_secret, self._scopes)
                self._expiry = time() + self._oauth_response["expires_in"] * 0.97
            elif self._cred_type == "client_id":
                self._oauth_response = oauth_refresh(self._acc_secret)
                self._scopes = self._oauth_response["scope"].split(" ")
                self._expiry = time() + self._oauth_response["expires_in"] * 0.97
    
    @property
    def token(self):
        self.refresh()
        return self._oauth_response['access_token']

    @property
    def headers(self):
        self.refresh()
        return {"Authorization": f"{self.token_type} {self.token}"}
    
    @property 
    def token_type(self):
        if self.cred_type == "api_key": 
            return "X-goog-api-key"
        return self._oauth_response["token_type"]
    
    @property
    def oauth_response(self):
        return self._oauth_response
    
    @property
    def cred_type(self):
        return self._cred_type
    
    @property
    def expiry(self):
        return self._expiry
    
    @property
    def scopes(self):
        return self._scopes
