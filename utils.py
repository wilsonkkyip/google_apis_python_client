import requests 
import pandas as pd 
from .credentials import Credential


def oauth_app(client_secret, scopes=None, port=8088):
    """
    This function builds an app for user authentication. It takes in the
    `client_secret`, the `scopes` that the users will be authenticated, and the
    `port`. The `client_secret` is the path to the JSON file that can be
    downloaded from the Google API console when creating the credentials.
    This function creates a temporary web-server on a specific port of the
    "localhost" and the url "http://localhost:{port}/" must also be specified
    on the Google API console when creating the credentials.

    Reference from "https://www.youtube.com/watch?v=vQQEaSnQ_bs" for details.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow
    if scopes is None:
        # Suggested scopes for google sheets, dirve
        scopes = [
            # Full control on Google Drive, Sheets, Slides, Docs and Apps Script
            "https://www.googleapis.com/auth/drive",
            # Full control on Google Calendar
            "https://www.googleapis.com/auth/calendar",
            # Full control on YouTube account
            "https://www.googleapis.com/auth/youtube",
            # Fetching YouTube comments
            "https://www.googleapis.com/auth/youtube.force-ssl",
            # View YouTube Reports and Analytics
            "https://www.googleapis.com/auth/yt-analytics.readonly",
            # "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
            # Full control on Google Mail
            "https://mail.google.com/",
            # Manage Googel Cloud
            "https://www.googleapis.com/auth/cloud-platform",
            # View GSuite directory
            "https://www.googleapis.com/auth/directory.readonly",
            # Full control on Apps Script
            "https://www.googleapis.com/auth/script.projects"
        ]

    flow = InstalledAppFlow.from_client_config(
        client_secret,
        scopes=scopes
    )

    flow.run_local_server(port=port, prompt="consent")
    return flow.credentials.to_json()



def list_all_gservices():
    """
    Google API Discovery Service allows service consumers to list the
    discovery metadata of all public APIs managed by the API Platform.

    The main objective of this function is to list out all the available API
    services provided by Google and their "ids" for further use.
    """
    url = "https://www.googleapis.com/discovery/v1/apis/"

    response = requests.get(url)
    return pd.DataFrame(response.json()["items"])


def get_latest_service_version(service_name):
    """
    This function takes in `service_name` (e.g. "sheets") and returns the latest
    version of the service.
    """
    servicesdf = list_all_gservices()
    return servicesdf["version"].loc[
        servicesdf["name"].str.lower() == service_name.lower()].max()


def split_method(method):
    """
    This function split the `method`,
    in form of "sheets:v4.spreadsheets.values.get",
    into (service, version, [resource, ..., method])
    """
    method = method.split(".")
    service_name, version = method[0].split(":")
    method = method[1:]
    method.reverse()
    return service_name, version, method


def get_service_details(service_name, version=None):
    """
    This function takes in the `service_name` (like "sheets", "drive", "youtube")
    and the `version` of the service and returns the service detail JSON from
    the following url:
    "https://www.googleapis.com/discovery/v1/apis/{service_name}/{version}/rest"
    """
    # https://stackoverflow.com/questions/10664868/where-can-i-find-a-list-of-scopes-for-googles-oauth-2-0-api
    version = version or get_latest_service_version(service_name)
    baseurl = "https://www.googleapis.com/discovery/v1/apis"
    url = f"{baseurl}/{service_name}/{version}/rest"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_service_scopes(service_name, version=None):
    """
    This function takes in the `service_name` (like "sheets", "drive", "youtube")
    and the `version` of the service and returns a list of scopes that are
    required by this service.
    """
    version = version or get_latest_service_version(service_name)
    response = get_service_details(service_name, version)
    return list(response["auth"]["oauth2"]["scopes"].keys())


def get_method_details_from_doc(method, doc):
    while len(method) > 1:
        doc = doc["resources"][method.pop()]
    doc = doc["methods"][method.pop()]
    return doc


def get_method_details(method):
    """
    This function takes in the `method` (in for of "sheets:v4.spreadsheets.values.get")
    and returns the details of the method, including the scopes required, the
    parameter(s) required and so on.
    """
    service_name, version, method = split_method(method)
    response = get_service_details(service_name, version)

    return get_method_details_from_doc(method, response)


def get_method_scopes(method):
    """
    This function takes in the `method` ("sheets:v4.spreadsheets.values.get")
    and returns required scopes.
    """
    response = get_method_details(method)
    return response["scopes"]


def num2letter(n):
    """Number to Excel-style column name, e.g., 1 = A, 26 = Z, 27 = AA, 703 = AAA."""
    name = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        name = chr(r + ord('A')) + name
    return name


def jq_lite(json_dict, query, default=None):
    """
    Query value from json dictionary.

    Parameters
    ----------
    json_dict: dict
        A json dictionary to be queried

    query: str
        Nested keys separated by "."
    
    default: any
        Default value if the keys cannot be found
    
    Examples
    --------
        json_dict = {
            "a": "A",
            "b": {"b1": "B1"},
            "c": [{"c1": "C1", "c2": "C2"}, {"c1": "CC1", "c2": "CC2"}, {"anything": "anything"}]
        }

        jq_lite(json_dict, "a")
        # 'A'

        jq_lite(json_dict, "b.b1")
        # 'B1'

        jq_lite(json_dict, "c.c2")
        # ['C2', 'CC2', None]
    """
    query = query.split(".") if type(query) is str else query
    query0 = query.pop(0)
    if type(json_dict) is dict:
        json_dict = json_dict.get(query0, default)
    elif type(json_dict) is list:
        json_dict = [jq_lite(jd, query0, default) for jd in json_dict]
    else:
        return None
    if len(query) > 0:
        json_dict = jq_lite(json_dict, query, default)
    return json_dict


class GoogleAuthBuilder(Credential):
    """
    A fundamental class for Google APIs. It inherits from `Credential` class.
    So it takes in 3 types of Google credentials: 
        1. API key
        2. Service account json (either path to json or json dictionary)
        3. OAuth client id json (either path to json or json dictionary)
    It has only two main methods: `build_params` and `request`. 

    Methods
    -------
    - build_params
        It takes in the API `service name`, `version`, `method`, and arguments 
        of the method and returns the required `http method`, `url`, `params` 
        and `body`. 
    
    - request
        With the response from `build_params`, this method sends out the API 
        request and returns the response from the API. 
    """
    def __init__(self, acc_secret):
        Credential.__init__(self, acc_secret)
        self._docs = dict()
    
    def _update_doc(self, method):
        """
        This class caches the updated "Google API Discovery" output each time 
        the methods are run. 
        """
        service, version, method = split_method(method=method)
        if f"{service}:{version}" not in self._docs:
            res = get_service_details(service, version)
            self._docs[f"{service}:{version}"] = res 
    
    def _fetch_docs(self, method):
        """
        Fetch from the cached "Google API Discovery" output and return a 
        document for the API service and method. 
        """
        service, version, method = split_method(method=method)
        service_doc = self._docs[f"{service}:{version}"]
        method_doc = get_method_details_from_doc(method, service_doc)
        return service_doc, method_doc
    
    def build_params(self, **kwargs):
        """
        Buiuld the required http method, url, body and params based on the 
        API method and "Google API Discovery" docs
        """
        locals = kwargs
        kwargs = locals.pop("kwargs", dict())
        self._update_doc(locals["method"])
        service_doc, method_doc = self._fetch_docs(locals["method"])
        url = service_doc["baseUrl"] + method_doc["path"]
        url = url.format(**locals)
        query_params = [k for k, v in method_doc["parameters"].items() if v["location"] == "query"]
        
        params = dict()
        for k in query_params:
            params[k] = locals.get(k) if locals.get(k) else kwargs.get(k)

        body = None
        if method_doc.get("request"):
            body = dict()
            body_doc = service_doc["schemas"][method_doc.get("request")["$ref"]]
            for k in body_doc["properties"].keys():
                if k in locals:
                    body[k] = locals[k]
                elif k in kwargs:
                    body[k] = kwargs[k]

        return service_doc, method_doc, method_doc["httpMethod"], url, params, body
    
    def request(self, method, url, params=None, body=None, **kwargs):
        """
        Send API request
        """
        self.refresh()
        args = {
            "method": method, "url": url, "headers": self.headers,
            "params": params, "json": body, **kwargs
        }
        response = requests.request(**args)

        if not response.ok:
            print(response.text)
            response.raise_for_status()

        if response.status_code == 204:
            return None

        return response.json()
