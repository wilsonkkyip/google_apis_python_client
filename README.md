# Python high level Google APIs client

- [Usage](#usage)
    - [Obtain client token JSON from client secret JSON](#obtain-client-token-json-from-client-secret-json)
    - [Initialise the `GoogleAuth` class](#initialise-the-googleauth-class)
    - [Class methods introduction](#class-methods-introduction)
    - [Google Drive APIs](#google-drive-apis)
        - [`cp` method](#cp-method)
        - [`ls` method](#ls-method)
        - [`findone` method](#findone-method)
        - [`rm` method](#rm-method)
        - [`ln` method](#ln-method)
        - [`mkdir` method](#mkdir-method)
        - [`mv` method](#mv-method)
        - [`upload_file` method](#upload_file-method)
        - [`download_file` method](#download_file-method)
    - [Google Sheets APIs](#google-sheets-apis)
        - [`create_spreadsheet` method](#create_spreadsheet-method)
        - [`get_sheets_info` method](#get_sheets_info-method)
        - [`batch_update_spreadsheet` method](#batch_update_spreadsheet-method)
        - [`update_sheet` method](#update_sheet-method)
        - [`get_sheet` method](#get_sheet-method)
        - [`clear_sheet` method](#clear_sheet-method)
        - [`append_sheet` method](#append_sheet-method)
        - [`get_sheet_values` method](#get_sheet_values-method)
    - [Miscellaneous YouTube functions](#miscellaneous-youtube-functions)
        - [`yt_vid_from_vurl` function](#yt_vid_from_vurl-function)
        - [`yt_cid_from_curl` function](#yt_cid_from_curl-function)
    - [YouTube Data API](#youtube-data-api)
        - [`list_videos` method](#list_videos-method)
        - [`list_channel` method](#list_channel-method)

This module offers a high level control on limited methods from the following APIs:

- Google Sheets API
- Google Drive API
- YouTube Data API

It also offers tools to build API parameters for all methods listed in the Discovery.

This module is built for some personal projects. It is not completed but sufficient for what I need. 

## Usage

This module supports three types of authentication methods: 

- API key
- Service account
- OAuth client id for web application

### Obtain client token JSON from client secret JSON

```python
import json 
from GoogleAuth.utils import oauth_app

with open("path_to_client_secret.json", "r") as f:
    client_secret = json.loads(f.read())

client_token = oauth_app(client_secret, scopes, port)

# Write the token to `client_token.json`.
with open("client_token.json", "w") as f:
    f.write(json.dumps(client_toen, indent=4))
```

### Initialise the `GoogleAuth` class

With `acc_secret` defined as one of the following:

1. String of an API key
2. Path string or JSON dict of service account JSON
3. Path string or JSON dict of `client_token.json`

```python
from GoogleAuth import GoogleAuth

gapi = GoogleAuth(acc_secret)
```

### Class methods introduction

- Google Sheets
    - `get_sheet`: Fetch spreadsheet values into pandas dataframe
    - `update_sheet`: Update spreadsheet values from pandas dataframe
    - `clear_sheet`: Clear values in spreadsheet
    - `append_sheet`: Append to spreadsheet from pandas dataframe
    - `get_spreadsheet`: Generic API call to get spreadsheet's metadata, 
                        including cell colors and more
    - `get_sheet_values`: Fetch cell values (mainly for fetching embedded urls)
    - `get_sheets_info`: Fetch basic info about each sheet (or tab) in spreadsheet.
    - `batch_update_spreadsheet`: Perform modifications on spreadsheet, 
                                e.g.: Add sheets, change cell colors etc.
    - `create_spreadsheet`: Create new spreadsheet and move to specific Googdle Drive folder.
- YouTube
    - `list_videos`: Fetch videos data from video_ids
    - `list_channels`: Fetch channels data from channel_ids
    - `list_playlist_items`: Generic API call to "youtube:v3.playlistItems.list"
    - `k_vid_before_date`: Fetch k videos data before specific date from playlist_id 
                            (usually its the playlist for the uploads from channel)
- Google Drive
    - `list_gdrive_files`: Generic API call to "drive:v3.files.list"
    - `find`: Search files from drive using the parameter `q`
    - `ls`: List files in a folder
    - `cp`: Copy a file
    - `findone`: Fetch metadata for a single file
    - `rm`: Remove a file (not Trash)
    - `credate_gdrive_files`: Generic API call to "drive:v3.files.create" and "drive:v3.files.update"
    - `ln`: Create a shortcut to a file
    - `mkdir`: Create a new folder
    - `mv`: Move (or rename) a file
    - `upload_file`: Upload a file from path or io.BytesIO
    - `download_file`: Download a file to a path or io.BytesIO

### Google Drive APIs

```python
folder_id1 = "1a-ghy0j47ePFcp9mOBUXpaLukULwJaXI"
folder_id2 = "1rqD-MXMZO_Xv9ETjEmfUiIe-r332lPk9"
```

#### `cp` method

```python
file_id = "1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD"
gapi.cp(
    fileId=file_id,
    name="copy_of_csv.csv",
    folderId=folder_id1,
    fields=["name", "id", "createdTime"]
)
# {
#     "id": "1cTffKHU7i67_kb3tbkHG4_tTcHdNV_Ld",
#     "name": "copy_of_csv.csv",
#     "createdTime": "2023-03-11T12:47:57.022Z"
# }
```

#### `ls` method

```python
gapi.ls(
    folderId=folder_id1,
    show_trashed=False
)
#                         md5Checksum  mimeType                                           owners   size                                 id             name               createdTime              modifiedTime
# 0  9b75560db14fbe6a5e86cb55f72faf70  text/csv  [{'emailAddress': '_______________@gmail.com'}]  60301  1cTffKHU7i67_kb3tbkHG4_tTcHdNV_Ld  copy_of_csv.csv  2023-03-11T12:47:57.022Z  2023-03-11T12:47:57.022Z
# 1  9b75560db14fbe6a5e86cb55f72faf70  text/csv  [{'emailAddress': '_______________@gmail.com'}]  60301  1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD      titanic.csv  2023-03-11T12:36:26.363Z  2023-03-11T12:36:06.000Z
```

#### `findone` method

```python
gapi.findone(
    fileId="1cTffKHU7i67_kb3tbkHG4_tTcHdNV_Ld",
    fields=["id", "name", "mimeType"]
)
# {
#     "id": "1cTffKHU7i67_kb3tbkHG4_tTcHdNV_Ld",
#     "name": "copy_of_csv.csv",
#     "mimeType": "text/csv"
# }
```

#### `rm` method 

```python
gapi.rm(
    fileId="1cTffKHU7i67_kb3tbkHG4_tTcHdNV_Ld"
)
# returns None

gapi.ls(folder_id1, show_trashed=True)
#                         md5Checksum  mimeType                                           owners   size                                 id         name  trashed               createdTime              modifiedTime
# 0  9b75560db14fbe6a5e86cb55f72faf70  text/csv  [{'emailAddress': '_______________@gmail.com'}]  60301  1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD  titanic.csv    False  2023-03-11T12:36:26.363Z  2023-03-11T12:36:06.000Z
```

#### `ln` method

```python
gapi.ln(
    targetId=folder_id2,
    name="folder2",
    folderId=folder_id1,
    fields=["id", "name", "mimeType"]
)
# {
#     "id": "130Pm24OXobY9_cwiQFMm0oFphTVTeyBy",
#     "name": "folder2",
#     "mimeType": "application/vnd.google-apps.shortcut"
# }

gapi.ls(
    folder_id1,
    fields=["id", "name", "mimeType"]
)
#                                mimeType                                 id         name
# 0  application/vnd.google-apps.shortcut  130Pm24OXobY9_cwiQFMm0oFphTVTeyBy      folder2
# 1                              text/csv  1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD  titanic.csv
```


#### `mkdir` method

```python
gapi.mkdir(
    folderName="folder3",
    folderId=folder_id1,
    fields=["id", "name", "mimeType", "parents"]
)
# {
#     "id": "17Oa8uDOOwli4n-c_nZqLbo9rjE2unG6l",
#     "name": "folder3",
#     "mimeType": "application/vnd.google-apps.folder",
#     "parents": [
#         "1a-ghy0j47ePFcp9mOBUXpaLukULwJaXI"
#     ]
# }

gapi.ls(
    folder_id1,
    fields=["id", "name", "mimeType"]
)
#                                mimeType                                 id         name
# 0    application/vnd.google-apps.folder  17Oa8uDOOwli4n-c_nZqLbo9rjE2unG6l      folder3
# 1  application/vnd.google-apps.shortcut  130Pm24OXobY9_cwiQFMm0oFphTVTeyBy      folder2
# 2                              text/csv  1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD  titanic.csv
```

#### `mv` method

```python
gapi.mv(
    fileId="17Oa8uDOOwli4n-c_nZqLbo9rjE2unG6l",
    folderId=folder_id2,
    fields=["id", "name", "parents"]
)
# {
#     "id": "17Oa8uDOOwli4n-c_nZqLbo9rjE2unG6l",
#     "name": "folder3",
#     "parents": [
#         "1rqD-MXMZO_Xv9ETjEmfUiIe-r332lPk9"
#     ]
# }


gapi.ls(
    folder_id1,
    fields=["id", "name", "mimeType"]
)
#                                mimeType                                 id         name
# 0  application/vnd.google-apps.shortcut  130Pm24OXobY9_cwiQFMm0oFphTVTeyBy      folder2
# 1                              text/csv  1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD  titanic.csv
```

#### `upload_file` method 

```python
new_json_dict = {
    "a": 1,
    "b": 2
}

with open("./new_dict.json", "w") as f:
    f.write(json.dumps(new_json_dict))

gapi.upload_file(
    fpath="./new_dict.json",
    name="new_dict_new_name.json",
    folderId=folder_id1
)
# {
#     "id": "1TJYNjsHEwJMPyxPZlaSeEXNikCDhuWS3",
#     "name": "new_dict_new_name.json",
#     "mimeType": "application/json",
#     "parents": [
#         "1a-ghy0j47ePFcp9mOBUXpaLukULwJaXI"
#     ],
#     "createdTime": "2023-03-11T13:27:17.248Z",
#     "md5Checksum": "8aacdb17187e6acf2b175d4aa08d7213",
#     "size": "16"
# }

gapi.ls(
    folder_id1,
    fields=["id", "name", "mimeType"]
)
#                                mimeType                                 id                    name
# 0                      application/json  1TJYNjsHEwJMPyxPZlaSeEXNikCDhuWS3  new_dict_new_name.json
# 1  application/vnd.google-apps.shortcut  130Pm24OXobY9_cwiQFMm0oFphTVTeyBy                 folder2
# 2                              text/csv  1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD             titanic.csv
```


```python
import io

new_json_dict = {
    "a": 1,
    "b": 2
}

with io.BytesIO() as fpath:
    fpath.write(json.dumps(new_json_dict).encode("utf-8"))
    gapi.upload_file(
        fpath=fpath,
        name="new_dict_byteio.json",
        folderId=folder_id2
    )
# {
#     "id": "1fYTXHbjjtz5AwsF84poFhEWulMx2vrbk",
#     "name": "new_dict_byteio.json",
#     "mimeType": "application/json",
#     "parents": [
#         "1rqD-MXMZO_Xv9ETjEmfUiIe-r332lPk9"
#     ],
#     "createdTime": "2023-03-11T13:39:25.555Z",
#     "md5Checksum": "8aacdb17187e6acf2b175d4aa08d7213",
#     "size": "16"
# }

gapi.ls(
    folder_id2,
    fields=["id", "name", "mimeType"]
)
#                              mimeType                                 id                  name
# 0                    application/json  1fYTXHbjjtz5AwsF84poFhEWulMx2vrbk  new_dict_byteio.json
# 1  application/vnd.google-apps.folder  17Oa8uDOOwli4n-c_nZqLbo9rjE2unG6l               folder3
```

#### `download_file` method

```python
json_dict_file_id = "1fYTXHbjjtz5AwsF84poFhEWulMx2vrbk"
gapi.download_file(
    fileId=json_dict_file_id,
    path="./saved_file.json"
)

with open("./saved_file.json", "r") as f:
    saved_file = json.loads(f.read())

saved_file
# {'a': 1, 'b': 2}
```

```python
import pandas as pd

csv_file_id = "1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD"
file = gapi.download_file(
    fileId=csv_file_id
)

pd.read_csv(file)
#      PassengerId  Survived  Pclass                                               Name     Sex   Age  SibSp  Parch            Ticket     Fare Cabin Embarked
# 0              1         0       3                            Braund, Mr. Owen Harris    male  22.0      1      0         A/5 21171   7.2500   NaN        S
# 1              2         1       1  Cumings, Mrs. John Bradley (Florence Briggs Th...  female  38.0      1      0          PC 17599  71.2833   C85        C
# 2              3         1       3                             Heikkinen, Miss. Laina  female  26.0      0      0  STON/O2. 3101282   7.9250   NaN        S
# 3              4         1       1       Futrelle, Mrs. Jacques Heath (Lily May Peel)  female  35.0      1      0            113803  53.1000  C123        S
# 4              5         0       3                           Allen, Mr. William Henry    male  35.0      0      0            373450   8.0500   NaN        S
# ..           ...       ...     ...                                                ...     ...   ...    ...    ...               ...      ...   ...      ...
# 886          887         0       2                              Montvila, Rev. Juozas    male  27.0      0      0            211536  13.0000   NaN        S
# 887          888         1       1                       Graham, Miss. Margaret Edith  female  19.0      0      0            112053  30.0000   B42        S
# 888          889         0       3           Johnston, Miss. Catherine Helen "Carrie"  female   NaN      1      2        W./C. 6607  23.4500   NaN        S
# 889          890         1       1                              Behr, Mr. Karl Howell    male  26.0      0      0            111369  30.0000  C148        C
# 890          891         0       3                                Dooley, Mr. Patrick    male  32.0      0      0            370376   7.7500   NaN        Q
```


### Google Sheets APIs

#### `create_spreadsheet` method

```python
gapi.create_spreadsheet(
    spreadsheet_title = "new spreadsheet",
    sheet_titles = ["first sheet", "second sheet"],
    folderId=folder_id1
)
# {
#     "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#     "properties": {
#         "title": "new spreadsheet",
#         "locale": "en_US",
#         "autoRecalc": "ON_CHANGE",
#         "timeZone": "Etc/GMT",
#         "defaultFormat": {...},
#         "spreadsheetTheme": {...}
#     },
#     "sheets": [
#         {
#             "properties": {
#                 "sheetId": 1081164414,
#                 "title": "first sheet",
#                 "index": 0,
#                 "sheetType": "GRID",
#                 "gridProperties": {
#                     "rowCount": 1000,
#                     "columnCount": 26
#                 }
#             }
#         },
#         {
#             "properties": {
#                 "sheetId": 1571346176,
#                 "title": "second sheet",
#                 "index": 1,
#                 "sheetType": "GRID",
#                 "gridProperties": {
#                     "rowCount": 1000,
#                     "columnCount": 26
#                 }
#             }
#         }
#     ],
#     "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE/edit"
# }

gapi.ls(folder_id1)
#                                   mimeType                                           owners   size                                            id                    name  trashed               createdTime              modifiedTime                       md5Checksum
# 0  application/vnd.google-apps.spreadsheet  [{'emailAddress': 'wilsonkkyip0506@gmail.com'}]   1024  1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE         new spreadsheet    False  2023-03-11T15:30:09.428Z  2023-03-11T15:30:10.010Z                               NaN
# 1                         application/json  [{'emailAddress': 'wilsonkkyip0506@gmail.com'}]     16             1TJYNjsHEwJMPyxPZlaSeEXNikCDhuWS3  new_dict_new_name.json    False  2023-03-11T13:27:17.248Z  2023-03-11T13:27:17.248Z  8aacdb17187e6acf2b175d4aa08d7213
# 2     application/vnd.google-apps.shortcut  [{'emailAddress': 'wilsonkkyip0506@gmail.com'}]    NaN             130Pm24OXobY9_cwiQFMm0oFphTVTeyBy                 folder2    False  2023-03-11T13:13:01.502Z  2023-03-11T13:13:01.502Z                               NaN
# 3                                 text/csv  [{'emailAddress': 'wilsonkkyip0506@gmail.com'}]  60301             1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD             titanic.csv    False  2023-03-11T12:36:26.363Z  2023-03-11T12:36:06.000Z  9b75560db14fbe6a5e86cb55f72faf70
```

#### `get_sheets_info` method

```python
spreadsheet_id = "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE"
gapi.get_sheets_info(spreadsheet_id)
#       sheetId         title  index sheetType  rowCount  columnCount  hidden
# 0  1081164414   first sheet      0      GRID      1000           26   False
# 1  1571346176  second sheet      1      GRID      1000           26   False
```

#### `batch_update_spreadsheet` method

```python
requests = [{
    "addSheet": {
        "properties": {
            "title": "third sheet"
        }
    }
}]

gapi.batch_update_spreadsheet(
    spreadsheetId=spreadsheet_id, 
    requests=requests
)
# {
#     "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#     "replies": [
#         {
#             "addSheet": {
#                 "properties": {
#                     "sheetId": 775831024,
#                     "title": "third sheet",
#                     "index": 2,
#                     "sheetType": "GRID",
#                     "gridProperties": {
#                         "rowCount": 1000,
#                         "columnCount": 26
#                     }
#                 }
#             }
#         }
#     ],
#     "updatedSpreadsheet": {
#         "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#         "properties": {
#             "title": "new spreadsheet",
#             "locale": "en_US",
#             "autoRecalc": "ON_CHANGE",
#             "timeZone": "Etc/GMT",
#             "defaultFormat": {...},
#             "spreadsheetTheme": {...}
#         },
#         "sheets": [
#             {
#                 "properties": {
#                     "sheetId": 1081164414,
#                     "title": "first sheet",
#                     "index": 0,
#                     "sheetType": "GRID",
#                     "gridProperties": {
#                         "rowCount": 1000,
#                         "columnCount": 26
#                     }
#                 }
#             },
#             {
#                 "properties": {
#                     "sheetId": 1571346176,
#                     "title": "second sheet",
#                     "index": 1,
#                     "sheetType": "GRID",
#                     "gridProperties": {
#                         "rowCount": 1000,
#                         "columnCount": 26
#                     }
#                 }
#             },
#             {
#                 "properties": {
#                     "sheetId": 775831024,
#                     "title": "third sheet",
#                     "index": 2,
#                     "sheetType": "GRID",
#                     "gridProperties": {
#                         "rowCount": 1000,
#                         "columnCount": 26
#                     }
#                 }
#             }
#         ],
#         "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE/edit"
#     }
# }

gapi.get_sheets_info(spreadsheet_id)
#       sheetId         title  index sheetType  rowCount  columnCount  hidden
# 0  1081164414   first sheet      0      GRID      1000           26   False
# 1  1571346176  second sheet      1      GRID      1000           26   False
# 2   775831024   third sheet      2      GRID      1000           26   False
```

#### `update_sheet` method

```python 
import pandas as pd 
csv_file_id = "1_Gdcsv7o_C7onQ6DVQxVNJjtXLeMeCFD"
df = pd.read_csv(gapi.download_file(csv_file_id))

df.head()
#    PassengerId  Survived  Pclass                                               Name     Sex   Age  SibSp  Parch            Ticket     Fare Cabin Embarked
# 0            1         0       3                            Braund, Mr. Owen Harris    male  22.0      1      0         A/5 21171   7.2500   NaN        S
# 1            2         1       1  Cumings, Mrs. John Bradley (Florence Briggs Th...  female  38.0      1      0          PC 17599  71.2833   C85        C
# 2            3         1       3                             Heikkinen, Miss. Laina  female  26.0      0      0  STON/O2. 3101282   7.9250   NaN        S
# 3            4         1       1       Futrelle, Mrs. Jacques Heath (Lily May Peel)  female  35.0      1      0            113803  53.1000  C123        S
# 4            5         0       3                           Allen, Mr. William Henry    male  35.0      0      0            373450   8.0500   NaN        S

spreadsheet_id = "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE"

ranges = [
    "'first sheet'!A:B",
    "'second sheet'!A:B",
]

values = [
    df.iloc[:,0:2],
    df.iloc[:,2:4]
]

gapi.update_sheet(
    spreadsheetId=spreadsheet_id,
    ranges=ranges,
    values=values,
    columns=True # if column names be also uploaded
)
# {
#     "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#     "totalUpdatedRows": 1784,
#     "totalUpdatedColumns": 4,
#     "totalUpdatedCells": 3568,
#     "totalUpdatedSheets": 2,
#     "responses": [
#         {
#             "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#             "updatedRange": "'first sheet'!A1:B892",
#             "updatedRows": 892,
#             "updatedColumns": 2,
#             "updatedCells": 1784
#         },
#         {
#             "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#             "updatedRange": "'second sheet'!A1:B892",
#             "updatedRows": 892,
#             "updatedColumns": 2,
#             "updatedCells": 1784
#         }
#     ]
# }
```

#### `get_sheet` method

```python
spreadsheet_id = "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE"

ranges = [
    "'first sheet'!A:B",
    "'second sheet'!A:B",
]

dfs = gapi.get_sheet(
    spreadsheetId=spreadsheet_id,
    ranges=ranges
)

dfs.keys()
# dict_keys(["'first sheet'!A1:B1000", "'second sheet'!A1:B1000"])

list(dfs.values())[0]
#      PassengerId  Survived
# 0              1         0
# 1              2         1
# 2              3         1
# 3              4         1
# 4              5         0
# ..           ...       ...
# 886          887         0
# 887          888         1
# 888          889         0
# 889          890         1
# 890          891         0

# [891 rows x 2 columns]
```

#### `clear_sheet` method

```python
spreadsheet_id = "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE"

ranges = [
    "'first sheet'!A:B",
    "'second sheet'!A:B",
]

gapi.clear_sheet(
    spreadsheetId=spreadsheet_id,
    ranges=ranges
)
# {
#     "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#     "clearedRanges": [
#         "'first sheet'!A1:B1000",
#         "'second sheet'!A1:B1000"
#     ]
# }
```

#### `append_sheet` method

```python
spreadsheet_id = "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE"
range_ = "'first sheet'"

df.head()
#    PassengerId  Survived  Pclass                                               Name     Sex   Age  SibSp  Parch            Ticket     Fare Cabin Embarked
# 0            1         0       3                            Braund, Mr. Owen Harris    male  22.0      1      0         A/5 21171   7.2500   NaN        S
# 1            2         1       1  Cumings, Mrs. John Bradley (Florence Briggs Th...  female  38.0      1      0          PC 17599  71.2833   C85        C
# 2            3         1       3                             Heikkinen, Miss. Laina  female  26.0      0      0  STON/O2. 3101282   7.9250   NaN        S
# 3            4         1       1       Futrelle, Mrs. Jacques Heath (Lily May Peel)  female  35.0      1      0            113803  53.1000  C123        S
# 4            5         0       3                           Allen, Mr. William Henry    male  35.0      0      0            373450   8.0500   NaN        S

gapi.append_sheet(
    spreadsheetId=spreadsheet_id, 
    range=range_,
    values=df,
    columns=True
)
# {
#     "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#     "updates": {
#         "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#         "updatedRange": "'first sheet'!A1:L892",
#         "updatedRows": 892,
#         "updatedColumns": 12,
#         "updatedCells": 10704
#     }
# }

gapi.get_sheet(
    spreadsheetId=spreadsheet_id, 
    ranges=range_
)
#      PassengerId  Survived  Pclass                                               Name     Sex Age  SibSp  Parch            Ticket     Fare Cabin Embarked
# 0              1         0       3                            Braund, Mr. Owen Harris    male  22      1      0         A/5 21171   7.2500              S
# 1              2         1       1  Cumings, Mrs. John Bradley (Florence Briggs Th...  female  38      1      0          PC 17599  71.2833   C85        C
# 2              3         1       3                             Heikkinen, Miss. Laina  female  26      0      0  STON/O2. 3101282   7.9250              S
# 3              4         1       1       Futrelle, Mrs. Jacques Heath (Lily May Peel)  female  35      1      0            113803  53.1000  C123        S
# 4              5         0       3                           Allen, Mr. William Henry    male  35      0      0            373450   8.0500              S
# ..           ...       ...     ...                                                ...     ...  ..    ...    ...               ...      ...   ...      ...
# 886          887         0       2                              Montvila, Rev. Juozas    male  27      0      0            211536  13.0000              S
# 887          888         1       1                       Graham, Miss. Margaret Edith  female  19      0      0            112053  30.0000   B42        S
# 888          889         0       3           Johnston, Miss. Catherine Helen "Carrie"  female          1      2        W./C. 6607  23.4500              S
# 889          890         1       1                              Behr, Mr. Karl Howell    male  26      0      0            111369  30.0000  C148        C
# 890          891         0       3                                Dooley, Mr. Patrick    male  32      0      0            370376   7.7500              Q

# [891 rows x 12 columns]
```

#### `get_sheet_values` method

```python
spreadsheet_id = "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE"
range_ = "'second sheet'!A:A"

values = [['=HYPERLINK("https://youtube.com", "LINK")'] for x in range(100)]

gapi.append_sheet(
    spreadsheetId=spreadsheet_id,
    range=range_,
    values=values,
    valueInputOption="USER_ENTERED"
)
# {
#     "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#     "updates": {
#         "spreadsheetId": "1PNkgib-UV3kPiTM0H-8oYCiTj3HKU76EoFqvhlvubGE",
#         "updatedRange": "'second sheet'!A1:A100",
#         "updatedRows": 100,
#         "updatedColumns": 1,
#         "updatedCells": 100
#     }
# }

gapi.get_sheet(
    spreadsheetId=spreadsheet_id,
    ranges=range_,
    columns=["0"]
)
#        0
# 0   LINK
# 1   LINK
# 2   LINK
# 3   LINK
# 4   LINK
# ..   ...
# 95  LINK
# 96  LINK
# 97  LINK
# 98  LINK
# 99  LINK

# [100 rows x 1 columns]

pd.Series(gapi.get_sheet_values(
    spreadsheetId=spreadsheet_id,
    ranges=range_,
    valueRenderOption="hyperlink"
))
# 0     https://youtube.com
# 1     https://youtube.com
# 2     https://youtube.com
# 3     https://youtube.com
# 4     https://youtube.com
#              ...         
# 95    https://youtube.com
# 96    https://youtube.com
# 97    https://youtube.com
# 98    https://youtube.com
# 99    https://youtube.com
# Length: 100, dtype: object
```

### Miscellaneous YouTube functions

#### `yt_vid_from_vurl` function

```python
urls = [
    "https://www.youtube.com/watch?v=pEfrdAtAmqk",
    "https://www.youtube.com/shorts/EUpWMSTHXJ0",
    "https://youtu.be/3vfum74ggHE"
]

yt_vid_from_vurl(urls)
# ['pEfrdAtAmqk', 'EUpWMSTHXJ0', '3vfum74ggHE']
```

#### `yt_cid_from_curl` function

```python
urls = [
    "https://www.youtube.com/channel/UCO22Xm0wVcgE1x9AwMCla1Q/videos",
    "https://www.youtube.com/AndySterkowitz/",
    "https://www.youtube.com/c/Coreyms/",
    "https://www.youtube.com/user/THiNKmediaTV/"
]

yt_cid_from_curl(urls)
# ['UCO22Xm0wVcgE1x9AwMCla1Q', 'UCZ9qFEC82qM6Pk-54Q4TVWA', 'UCCezIgC97PvUuR4_gbFUs5g', 'UCGxjDWAN1KwrkXYVi8CXtjQ']
```

### YouTube Data API

#### `list_videos` method

```python 
urls = [
    "https://www.youtube.com/watch?v=pEfrdAtAmqk",
    "https://www.youtube.com/shorts/EUpWMSTHXJ0",
    "https://youtu.be/3vfum74ggHE"
]

vids = yt_vid_from_vurl(urls)

gapi.list_videos(vids)
#             kind           id           publishedAt                 channelId                                              title  ... likeCount favoriteCount commentCount topicIds                                    topicCategories
# 0  youtube#video  pEfrdAtAmqk  2022-08-24T17:05:46Z  UCsBjURrPoezykLs9EqgamOA                         God-Tier Developer Roadmap  ...  163328.0           0.0       7664.0     None  [https://en.wikipedia.org/wiki/Knowledge, http...
# 1  youtube#video  EUpWMSTHXJ0  2022-12-22T13:30:05Z  UCg37hi6mXHpdNCKA80HOSyQ  This boy saves the honor of this girl | FIGHT ...  ...   34119.0           0.0        577.0     None      [https://en.wikipedia.org/wiki/Entertainment]
# 2  youtube#video  3vfum74ggHE  2022-02-20T16:32:41Z  UCbXgNpp0jedKWcQiULLbDTA  I built the same app 3 times | Which Python Fr...  ...   12134.0           0.0        411.0     None          [https://en.wikipedia.org/wiki/Knowledge]
```

#### `list_channel` method

```python
urls = [
    "https://www.youtube.com/channel/UCO22Xm0wVcgE1x9AwMCla1Q/videos",
    "https://www.youtube.com/AndySterkowitz/",
    "https://www.youtube.com/c/Coreyms/",
    "https://www.youtube.com/user/THiNKmediaTV/"
]

cids = yt_cid_from_curl(urls)

gapi.list_channels(cids)
#               kind                        id            title                                        description        customUrl  ... subscriberCount hiddenSubscriberCount videoCount                          topicIds                                    topicCategories
# 0  youtube#channel  UCO22Xm0wVcgE1x9AwMCla1Q     MISS-K-DRAMA  Everything you need to know about the korean e...    @miss-k-drama  ...        111000.0                 False      342.0    [/m/02jjt, /m/02vxn, /m/0f2f9]  [https://en.wikipedia.org/wiki/Entertainment, ...
# 1  youtube#channel  UCZ9qFEC82qM6Pk-54Q4TVWA  Andy Sterkowitz                                                     @andysterkowitz  ...        331000.0                 False      152.0  [/m/01k8wb, /m/07c1v, /m/019_rr]  [https://en.wikipedia.org/wiki/Knowledge, http...
# 2  youtube#channel  UCCezIgC97PvUuR4_gbFUs5g    Corey Schafer  Welcome to my Channel. This channel is focused...         @coreyms  ...       1080000.0                 False      231.0  [/m/01k8wb, /m/07c1v, /m/019_rr]  [https://en.wikipedia.org/wiki/Knowledge, http...
# 3  youtube#channel  UCGxjDWAN1KwrkXYVi8CXtjQ      Think Media  Thanks for checking out Think Media on YouTube...    @thinkmediatv  ...       2390000.0                 False     1531.0             [/m/07c1v, /m/019_rr]  [https://en.wikipedia.org/wiki/Technology, htt...
```



