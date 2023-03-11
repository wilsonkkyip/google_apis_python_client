import asyncio 
import httpx
import json 
import pandas as pd 
import numpy as np
import os 
import io 
import re
import mimetypes
from requests import request
from itertools import chain
from datetime import datetime, timedelta
from .utils import num2letter, jq_lite, GoogleAuthBuilder


class GoogleAuth(GoogleAuthBuilder):
    """
    A class with commonly used Google APIs as methods

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
    Google Sheets
        - get_sheet: Fetch spreadsheet values into pandas dataframe
        - update_sheet: Update spreadsheet values from pandas dataframe
        - clear_sheet: Clear values in spreadsheet
        - append_sheet: Append to spreadsheet from pandas dataframe
        - get_spreadsheet: Generic API call to get spreadsheet's metadata, 
                           including cell colors and more
        - get_sheet_values: Fetch cell values (mainly for fetching embedded urls)
        - get_sheets_info: Fetch basic info about each sheet (or tab) in spreadsheet.
        - batch_update_spreadsheet: Perform modifications on spreadsheet, 
                                    e.g.: Add sheets, change cell colors etc.
        - create_spreadsheet: Create new spreadsheet and move to specific Googdle Drive folder.
    YouTube
        - list_videos: Fetch videos data from video_ids
        - list_channels: Fetch channels data from channel_ids
        - list_playlist_items: Generic API call to "youtube:v3.playlistItems.list"
        - k_vid_before_date: Fetch k videos data before specific date from playlist_id 
                             (usually its the playlist for the uploads from channel)
    Google Drive
        - list_gdrive_files: Generic API call to "drive:v3.files.list"
        - find: Search files from drive using the parameter `q`
        - ls: List files in a folder
        - cp: Copy a file
        - findone: Fetch metadata for a single file
        - rm: Remove a file (not Trash)
        - credate_gdrive_files: Generic API call to "drive:v3.files.create" and "drive:v3.files.update"
        - ln: Create a shortcut to a file
        - mkdir: Create a new folder
        - mv: Move (or rename) a file
        - upload_file: Upload a file from path or io.BytesIO
        - download_file: Download a file to a path or io.BytesIO
    
    Scopes
    ------
    [
        # Full control on Google Drive, Sheets, Slides, Docs and Apps Script
        "https://www.googleapis.com/auth/drive",
        # Full control on YouTube account
        "https://www.googleapis.com/auth/youtube"
    ]
    """
    def get_sheet(self, spreadsheetId, ranges, columns=None, 
                  valueRenderOption="UNFORMATTED_VALUE", 
                  dateTimeRenderOption="SERIAL_NUMBER", 
                  majorDimension="ROWS", **kwargs):
        """
        DESCRIPTION:
            The [A1 notation or R1C1 notation](/sheets/api/guides/concepts#cell) of
            the range to retrieve values from.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        \n\n
        PARAMETERS:
            spreadsheetId: string
                        The ID of the spreadsheet to retrieve data from.
            \n
            ranges[]: string
                    The [A1 notation or R1C1 notation](
                    /sheets/api/guides/concepts#cell) of the range to retrieve
                    values from.
            \n
            valueRenderOption: enum
                            How values should be represented in the output.
                            The default render option is FORMATTED_VALUE.
                FORMATTED_VALUE - Values will be calculated & formatted in the
                                reply according to the cell's formatting.
                                Formatting is based on the spreadsheet's locale,
                                not the requesting user's locale. For example,
                                if `A1` is `1.23` and `A2` is `=A1` and formatted
                                as currency, then `A2` would return `"$1.23"`.
                UNFORMATTED_VALUE - Values will be calculated, but not formatted in
                                    the reply. For example, if `A1` is `1.23` and `
                                    A2` is `=A1` and formatted as currency, then `
                                    A2` would return the number `1.23`.
                FORMULA - Values will not be calculated. The reply will include the
                        formulas. For example, if `A1` is `1.23` and `A2` is `=A1`
                        and formatted as currency, then A2 would return `"=A1"`.
            \n
            dateTimeRenderOption: enum
                                How dates, times, and durations should be
                                represented in the output. This is ignored if
                                value_render_option is FORMATTED_VALUE. The
                                default dateTime render option is SERIAL_NUMBER.
                SERIAL_NUMBER - Instructs date, time, datetime, and duration
                                fields to be output as doubles in \"serial
                                number\" format, as popularized by Lotus 1-2-3.
                                The whole number portion of the value (left of
                                the decimal) counts the days since December 30th
                                1899. The fractional portion (right of the
                                decimal) counts the time as a fraction of the
                                day. For example, January 1st 1900 at noon would
                                be 2.5, 2 because it's 2 days after December 30th
                                1899, and .5 because noon is half a day. February
                                1st 1900 at 3pm would be 33.625. This correctly
                                treats the year 1900 as not a leap year.
                FORMATTED_STRING - Instructs date, time, datetime, and duration
                                fields to be output as strings in their given
                                number format (which depends on the spreadsheet
                                locale).
        """
        method = "sheets:v4.spreadsheets.values.batchGet"
        ranges = [ranges] if type(ranges) is str else list(ranges) 
        
        if columns:
            columns = list(columns) if type(columns) is not str else [columns]
            if len(ranges) == 1 and ((not hasattr(columns[0], "__iter__")) or type(columns[0]) is str):
                columns = [columns]
        
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        response = self.request(method=method, url=url, params=params, body=body)
        
        if kwargs.get("raw_output") or majorDimension == "COLUMNS":
            return response 
        
        f = "valueRanges.values"
        output = []
        for i, x in enumerate(jq_lite(response, f)):
            if columns:
                output.append(pd.DataFrame(x, columns=columns[i]))
            else:
                output.append(pd.DataFrame(x[1:], columns=x[0]))
        
        if len(output) == 1:
            output = output[0]
        else:
            output = dict(zip(
                [x["range"] for x in response["valueRanges"]],
                output
            ))

        return output
    
    def update_sheet(self, spreadsheetId, ranges, values, columns=True,
                     majorDimension="ROWS",
                     valueInputOption="RAW",
                     includeValuesInResponse=False,
                     responseValueRenderOption="UNFORMATTED_VALUE",
                     responseDateTimeRenderOption="SERIAL_NUMBER", **kwargs):
        """
        DESCRIPTION:
            Sets values in one or more ranges of a spreadsheet. The caller must
            specify the spreadsheet ID, a valueInputOption, and one or more
            ValueRanges.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets"
        \n\n
        PARAMETERS:
            spreadsheetId: string
                        "The ID of the spreadsheet to update.
            \n
            ranges[]: string
                    The [A1 notation](/sheets/api/guides/concepts#cell) of the
                    values to update.
            \n
            values[][]: array
                        The data that was read or to be written. This is an array
                        of arrays, the outer array representing all the data and
                        each inner array representing a major dimension. Each item
                        in the inner array corresponds with one cell. For output,
                        empty trailing rows and columns will not be included. For
                        input, supported value types are: bool, string, and double.
                        Null values will be skipped. To set a cell to an empty
                        value, set the string value to an empty string.
            \n
            columns: bool
                    When `values` is a pandas.DataFrame, the method will convert 
                    it into a 2d array. If this parameter is set true, the 
                    column names will also be included in the 2d array.
            \n
            majorDimension: enum
                            The major dimension of the values. For output, if
                            the spreadsheet data is: `A1=1,B1=2,A2=3,B2=4`,
                            then requesting `range=A1:B2,majorDimension=ROWS`
                            will return `[[1,2],[3,4]]`, whereas requesting `
                            range=A1:B2,majorDimension=COLUMNS` will
                            return `[[1,3],[2,4]]`. For input, with `range=A1:
                            B2,majorDimension=ROWS` then `[[1,2],[3,4]]` will
                            set `A1=1,B1=2,A2=3,B2=4`. With `range=A1:B2,
                            majorDimension=COLUMNS` then `[[1,2],[3,4]]` will
                            set `A1=1,B1=3,A2=2,B2=4`. When writing, if this
                            field is not set, it defaults to ROWS.
                DIMENSION_UNSPECIFIED - The default value, do not use.
                ROWS - Operates on the rows of a sheet.
                COLUMNS - Operates on the columns of a sheet.
            \n
            valueInputOption: enum
                            How the input data should be interpreted.
                INPUT_VALUE_OPTION_UNSPECIFIED - Default input value. This
                                                value must not be used.
                RAW - The values the user has entered will not be
                    parsed and will be stored as-is.
                USER_ENTERED - The values will be parsed as if the user typed
                            them into the UI. Numbers will stay as numbers,
                            but strings may be converted to numbers, dates,
                            etc. following the same rules that are applied
                            when entering text into a cell via the Google
                            Sheets UI.
            \n
            includeValuesInResponse: bool
                                    Determines if the update response
                                    should include the values of the cells
                                    that were updated. By default,
                                    responses do not include the updated
                                    values. If the range to write was
                                    larger than the range actually written,
                                    the response includes all values in the
                                    requested range (excluding trailing
                                    empty rows and columns).
            \n
            responseValueRenderOption: enum
                                    Determines how values in the response
                                    should be rendered. The default render
                                    option is FORMATTED_VALUE.
                FORMATTED_VALUE - Values will be calculated & formatted in the
                                reply according to the cell's formatting.
                                Formatting is based on the spreadsheet's locale,
                                not the requesting user's locale. For example,
                                if `A1` is `1.23` and `A2` is `=A1` and formatted
                                as currency, then `A2` would return `"$1.23"`.
                UNFORMATTED_VALUE - Values will be calculated, but not formatted in
                                    the reply. For example, if `A1` is `1.23` and `
                                    A2` is `=A1` and formatted as currency, then `
                                    A2` would return the number `1.23`.
                FORMULA - Values will not be calculated. The reply will include the
                        formulas. For example, if `A1` is `1.23` and `A2` is `=A1`
                        and formatted as currency, then A2 would return `"=A1"`.
            \n
            responseDateTimeRenderOption: enum
                                        Determines how dates, times, and
                                        durations in the response should be
                                        rendered. This is ignored if
                                        response_value_render_option is
                                        FORMATTED_VALUE. The default dateTime
                                        render option is SERIAL_NUMBER.
                SERIAL_NUMBER - Instructs date, time, datetime, and duration
                                fields to be output as doubles in \"serial
                                number\" format, as popularized by Lotus 1-2-3.
                                The whole number portion of the value (left of
                                the decimal) counts the days since December 30th
                                1899. The fractional portion (right of the
                                decimal) counts the time as a fraction of the
                                day. For example, January 1st 1900 at noon would
                                be 2.5, 2 because it's 2 days after December 30th
                                1899, and .5 because noon is half a day. February
                                1st 1900 at 3pm would be 33.625. This correctly
                                treats the year 1900 as not a leap year.
                FORMATTED_STRING - Instructs date, time, datetime, and duration
                                fields to be output as strings in their given
                                number format (which depends on the spreadsheet
                                locale).
        """
        method = "sheets:v4.spreadsheets.values.batchUpdate"
        ranges = [ranges] if type(ranges) is str else list(ranges)

        if type(values) is pd.core.frame.DataFrame:
            values = [values]

        for i, v in enumerate(values):
            if type(v) is pd.core.frame.DataFrame:
                c = [list(v.columns)] if columns else []
                values[i] = c + v.fillna("").to_numpy().tolist()
            
        if len(ranges) != len(values):
            raise Exception("len(ranges) != len(values)")
        
        data = []
        for r, v in zip(ranges, values):
            data.append({
                "range": r,
                "majorDimension": majorDimension,
                "values": v
            })
        
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        response = self.request(method=method, url=url, params=params, body=body)

        return response
    

    def clear_sheet(self, spreadsheetId, ranges, **kwargs):
        """
        DESCRIPTION:
            Clears values from a spreadsheet. The caller must specify the
            spreadsheet ID and range. Only values are cleared -- all other
            properties of the cell (such as formatting, data validation, etc..)
            are kept.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets"
        \n\n
        PARAMETERS:
            spreadsheetId: string
                        The ID of the spreadsheet to update.
            \n
            ranges: string[]
                    The [A1 notation or R1C1 notation](
                    /sheets/api/guides/concepts#cell) of the values to clear.
        """
        method = "sheets:v4.spreadsheets.values.batchClear"
        ranges = [ranges] if type(ranges) is str else list(ranges) 
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        response = self.request(method=method, url=url, params=params, body=body)
        return response
    
    def append_sheet(self, spreadsheetId, range, values, columns=False,
                     majorDimension="ROWS",
                     insertDataOption="INSERT_ROWS",
                     valueInputOption="RAW",
                     includeValuesInResponse=False,
                     responseValueRenderOption="UNFORMATTED_VALUE",
                     responseDateTimeRenderOption="SERIAL_NUMBER", **kwargs):
        """
        DESCRIPTION:
            Appends values to a spreadsheet. The input range is used to search
            for existing data and find a "table" within that range. Values will
            be appended to the next row of the table, starting with the first
            column of the table. See the [guide](
            /sheets/api/guides/values#appending_values) and [sample code](
            /sheets/api/samples/writing#append_values) for specific details of
            how tables are detected and data is appended. The caller must specify
            the spreadsheet ID, range, and a valueInputOption. The `
            valueInputOption` only controls how the input data will be added to
            the sheet (column-wise or row-wise), it does not influence what cell
            the data starts being written to.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets"
        \n\n
        PARAMETERS:
            spreadsheetId: string
                        The ID of the spreadsheet to update.
            \n
            range_: string
                    The [A1 notation](/sheets/api/guides/concepts#cell) of a
                    range to search for a logical table of data. Values are
                    appended after the last row of the table.
            \n
            values: array[]
                    The data that was read or to be written. This is an array
                    of arrays, the outer array representing all the data and
                    each inner array representing a major dimension. Each item
                    in the inner array corresponds with one cell. For output,
                    empty trailing rows and columns will not be included. For
                    input, supported value types are: bool, string, and double.
                    Null values will be skipped. To set a cell to an empty
                    value, set the string value to an empty string.
            \n
            columns: bool
                    When `values` is a pandas.DataFrame, the method will convert 
                    it into a 2d array. If this parameter is set true, the 
                    column names will also be included in the 2d array.
            \n
            majorDimension: enum
                            The major dimension of the values. For output, if
                            the spreadsheet data is: `A1=1,B1=2,A2=3,B2=4`,
                            then requesting `range=A1:B2,majorDimension=ROWS`
                            will return `[[1,2],[3,4]]`, whereas requesting `
                            range=A1:B2,majorDimension=COLUMNS` will
                            return `[[1,3],[2,4]]`. For input, with `range=A1:
                            B2,majorDimension=ROWS` then `[[1,2],[3,4]]` will
                            set `A1=1,B1=2,A2=3,B2=4`. With `range=A1:B2,
                            majorDimension=COLUMNS` then `[[1,2],[3,4]]` will
                            set `A1=1,B1=3,A2=2,B2=4`. When writing, if this
                            field is not set, it defaults to ROWS.
                DIMENSION_UNSPECIFIED - The default value, do not use.
                ROWS - Operates on the rows of a sheet.
                COLUMNS - Operates on the columns of a sheet.
            \n
            insertDataOption: enum
                            How the input data should be inserted.
                OVERWRITE - The new data overwrites existing data in the
                            areas it is written. (Note: adding data to the
                            end of the sheet will still insert new rows or
                            columns so the data can be written.)
                INSERT_ROWS - Rows are inserted for the new data.
            \n
            valueInputOption: enum
                            How the input data should be interpreted.
                INPUT_VALUE_OPTION_UNSPECIFIED - Default input value. This value
                                                must not be used.
                RAW - The values the user has entered will not be parsed and will
                    be stored as-is.
                USER_ENTERED - The values will be parsed as if the user typed
                            them into the UI. Numbers will stay as numbers,
                            but strings may be converted to numbers, dates,
                            etc. following the same rules that are applied
                            when entering text into a cell via the Google
                            Sheets UI.
            \n
            includeValuesInResponse: bool
                                    Determines if the update response
                                    should include the values of the cells
                                    that were updated. By default,
                                    responses do not include the updated
                                    values. If the range to write was
                                    larger than the range actually written,
                                    the response includes all values in the
                                    requested range (excluding trailing
                                    empty rows and columns).
            \n
            responseValueRenderOption: enum
                                    Determines how values in the response
                                    should be rendered. The default render
                                    option is FORMATTED_VALUE.
                FORMATTED_VALUE - Values will be calculated & formatted in the
                                reply according to the cell's formatting.
                                Formatting is based on the spreadsheet's locale,
                                not the requesting user's locale. For example,
                                if `A1` is `1.23` and `A2` is `=A1` and formatted
                                as currency, then `A2` would return `"$1.23"`.
                UNFORMATTED_VALUE - Values will be calculated, but not formatted in
                                    the reply. For example, if `A1` is `1.23` and `
                                    A2` is `=A1` and formatted as currency, then `
                                    A2` would return the number `1.23`.
                FORMULA - Values will not be calculated. The reply will include the
                        formulas. For example, if `A1` is `1.23` and `A2` is `=A1`
                        and formatted as currency, then A2 would return `"=A1"`.
            \n
            responseDateTimeRenderOption: enum
                                        Determines how dates, times, and
                                        durations in the response should be
                                        rendered. This is ignored if
                                        response_value_render_option is
                                        FORMATTED_VALUE. The default dateTime
                                        render option is SERIAL_NUMBER.
                SERIAL_NUMBER - Instructs date, time, datetime, and duration
                                fields to be output as doubles in \"serial
                                number\" format, as popularized by Lotus 1-2-3.
                                The whole number portion of the value (left of
                                the decimal) counts the days since December 30th
                                1899. The fractional portion (right of the
                                decimal) counts the time as a fraction of the
                                day. For example, January 1st 1900 at noon would
                                be 2.5, 2 because it's 2 days after December 30th
                                1899, and .5 because noon is half a day. February
                                1st 1900 at 3pm would be 33.625. This correctly
                                treats the year 1900 as not a leap year.
                FORMATTED_STRING - Instructs date, time, datetime, and duration
                                fields to be output as strings in their given
                                number format (which depends on the spreadsheet
                                locale).
        """
        method = "sheets:v4.spreadsheets.values.append"
        if type(values) is pd.core.frame.DataFrame:
            c = [list(values.columns)] if columns else []
            values = c + values.fillna("").to_numpy().tolist()
        
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        response = self.request(method=method, url=url, params=params, body=body)
        return response
    
    def get_spreadsheet(self, spreadsheetId, ranges=None, fields=None,
                        includeGridData=True, **kwargs):
        """
        DESCRIPTION:
            Returns the spreadsheet at the given ID. The caller must specify the
            spreadsheet ID. By default, data within grids is not returned. You
            can include grid data in one of 2 ways: * Specify a field mask
            listing your desired fields using the `fields` URL parameter in HTTP
            * Set the includeGridData URL parameter to true. If a field mask is
            set, the `includeGridData` parameter is ignored For large
            spreadsheets, as a best practice, retrieve only the specific
            spreadsheet fields that you want. To retrieve only subsets of
            spreadsheet data, use the ranges URL parameter. Ranges are specified
            using [A1 notation](/sheets/api/guides/concepts#cell). You can define
            a single cell (for example, `A1`) or multiple cells (for example, `A1:
            D5`). You can also get cells from other sheets within the same
            spreadsheet (for example, `Sheet2!A1:C4`) or retrieve multiple ranges
            at once (for example, `?ranges=A1:D5&ranges=Sheet2!A1:C4`). Limiting
            the range returns only the portions of the spreadsheet that intersect
            the requested ranges.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        \n\n
        PARAMETERS:
            spreadsheetId: string
                        The spreadsheet to request.
        \n
            ranges: string[]
                    The ranges to retrieve from the spreadsheet.
        \n
            fields: string
                    https://stackoverflow.com/questions/46879715/get-hyperlink-from-a-cell-in-google-sheet-api-v4
            includeGridData: bool
                            True if grid data should be returned. This parameter
                            is ignored if a field mask was set in the request.
        """
        method = "sheets:v4.spreadsheets.get"
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        if fields:
            params["fields"] = fields
        response = self.request(method=method, url=url, params=params, body=body)
        return response


    def get_sheet_values(self, spreadsheetId, ranges, valueRenderOption, metadata=False, **kwargs):
        """
        Extract values in a spreadsheet with different valueRenderOption
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        \n\n
        PARAMETERS:
            spreadsheetId: string
                        The spreadsheet to request.
            \n
            ranges: string[]
                    The ranges to retrieve from the spreadsheet.
            \n
            valueRenderOption: string[]
                            Currently support 4:
                            [
                                "userEnteredValue", "effectiveValue",
                                "formattedValue", "hyperlink"
                            ]
                            For more reference:
                            https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#CellData
        """
        ranges = [ranges] if type(ranges) is str else list(ranges)
        valueRenderOption = [valueRenderOption] if type(valueRenderOption) is str else list(valueRenderOption)
        
        fields = f"sheets(properties,data(startRow,startColumn,(rowData(values({','.join(valueRenderOption)})))))"
        response = self.get_spreadsheet(spreadsheetId, ranges, fields=fields)

        if kwargs.get("raw_output"):
            return response
        
        sheet_titles_q = "sheets.properties.title"
        sheet_startRows_q = "sheets.data.startRow"
        sheet_startColumns_q = "sheets.data.startColumn"
        userEnteredValue_q = "sheets.data.rowData.values.userEnteredValue"
        effectiveValue_q = "sheets.data.rowData.values.effectiveValue"
        formattedValue_q = "sheets.data.rowData.values.formattedValue"
        hyperlink_q = "sheets.data.rowData.values.hyperlink"

        sheet_titles = jq_lite(response, sheet_titles_q)
        sheet_startRows = jq_lite(response, sheet_startRows_q, 0)
        sheet_startColumns = jq_lite(response, sheet_startColumns_q, 0)
        sheet_userEnteredValue = jq_lite(response, userEnteredValue_q)
        sheet_effectiveValue = jq_lite(response, effectiveValue_q)
        sheet_formattedValue = jq_lite(response, formattedValue_q)
        sheet_hyperlink = jq_lite(response, hyperlink_q)

        sheet_ranges = []
        for i, (cs, rs) in enumerate(zip(sheet_startColumns, sheet_startRows)):
            range_ = []
            for j, (c, r) in enumerate(zip(cs, rs)):
                max_col = max([len(x) for x in sheet_effectiveValue[i][j]])
                max_row = len(sheet_effectiveValue[i][j])
                end_col = c + max_col - 1
                end_row = r + max_row - 1
                initial_range = f"{num2letter(c + 1)}{r + 1}"
                final_range = f"{num2letter(end_col + 1)}{end_row + 1}"
                range_.append(
                    f"'{sheet_titles[i]}'!{initial_range}:{final_range}"
                )
            sheet_ranges.append(range_)
        
        sheet_ranges = list(chain(*sheet_ranges))

        if not metadata and (len(valueRenderOption) == 1) and (len(sheet_ranges) == 1):
            result = locals().get("sheet_" + valueRenderOption[0])[0][0]
            if max_col > 1:
                return result 
            return [x[0] for x in result]

        result = {}
        for v in valueRenderOption:
            values = list(chain(*locals().get("sheet_" + v)))
            result[v] = dict(zip(sheet_ranges, values))

        return result
    
    def get_sheets_info(self, spreadsheetId):
        """
        Fetch basic info for the sheets in a spreadsheet.
        """
        fields = "sheets.properties(sheetId,title,index,sheetType,gridProperties(rowCount,columnCount),hidden)"
        response = self.get_spreadsheet(spreadsheetId, fields=fields)

        outdf = []
        for i in range(len(response["sheets"])):
            properties = response["sheets"][i]["properties"]
            outdf.append(
                {
                    "sheetId": properties["sheetId"],
                    "title": properties["title"],
                    "index": properties["index"],
                    "sheetType": properties["sheetType"],
                    "rowCount": properties["gridProperties"]["rowCount"],
                    "columnCount": properties["gridProperties"]["columnCount"],
                    "hidden": properties.get("hidden", False)
                }
            )

        outdf = pd.DataFrame(outdf)
        return outdf
    

    def batch_update_spreadsheet(self, spreadsheetId, requests,
                                 includeSpreadsheetInResponse=True,
                                 responseRanges=None, responseIncludeGridData=False,
                                 **kwargs):
        """
        DESCRIPTION:
            Applies one or more updates to the spreadsheet. Each request is
            validated before being applied. If any request is not valid then the
            entire request will fail and nothing will be applied. Some requests
            have replies to give you some information about how they are applied.
            The replies will mirror the requests. For example, if you applied 4
            updates and the 3rd one had a reply, then the response will have 2
            empty replies, the actual reply, and another empty reply, in that
            order. Due to the collaborative nature of spreadsheets, it is not
            guaranteed that the spreadsheet will reflect exactly your changes
            after this completes, however it is guaranteed that the updates in
            the request will be applied together atomically. Your changes may be
            altered with respect to collaborator changes. If there are no
            collaborators, the spreadsheet should reflect your changes.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets"
        \n\n
        PARAMETERS:
            spreadsheetId: string
                        The spreadsheet to apply the updates to.
            \n
            requests[]: object
                        A list of updates to apply to the spreadsheet. Requests will
                        be applied in the order they are specified. If any request
                        is not valid, no requests will be applied.
            \n
            includeSpreadsheetInResponse: bool
                                        Determines if the update response should
                                        include the spreadsheet resource.
            \n
            responseRanges: string[]
                            Limits the ranges included in the response
                            spreadsheet. Meaningful only if
                            include_spreadsheet_in_response is 'true'.
            \n
            responseIncludeGridData: bool
                                    True if grid data should be returned.
                                    Meaningful only if
                                    include_spreadsheet_in_response is 'true'.
                                    This parameter is ignored if a field mask was
                                    set in the request.
        """
        method = "sheets:v4.spreadsheets.batchUpdate"
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        if kwargs.get("fields"):
            params["fields"] = kwargs.get("fields")
        response = self.request(method=method, url=url, params=params, body=body)
        return response
    

    def create_spreadsheet(self, spreadsheet_title=None, sheet_titles=None,
                           autoRecalc=None, folderId=None, **kwargs):
        """
        DESCRIPTION:
            Creates a spreadsheet, returning the newly created spreadsheet.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets"
        \n\n
        PARAMETERS:
            spreadsheet_title: string
                            The title of the spreadsheet.
            \n
            sheet_titles: string[]
                        The name of the sheet.
            \n
            autoRecalc: enum
                        The amount of time to wait before volatile functions are
                        recalculated.
                RECALCULATION_INTERVAL_UNSPECIFIED - Default value. This value must
                                                    not be used.
                ON_CHANGE - Volatile functions are updated on every change.
                MINUTE - Volatile functions are updated on every change and every
                        minute.
                HOUR - Volatile functions are updated on every change and hourly.
            \n
            folderId: string
                    The ID of the folder which the spreadesheet will be moved to.
        """
        method = "sheets:v4.spreadsheets.create"

        properties = dict()
        if spreadsheet_title:
            properties["title"] = spreadsheet_title
        if autoRecalc:
            properties["autoRecalc"] = autoRecalc
        
        properties["timeZone"] = kwargs.get("timeZone", "GMT")

        sheet_titles = [sheet_titles] if type(sheet_titles) is str else sheet_titles
        sheets = []
        if sheet_titles:
            for i, x in enumerate(sheet_titles):
                sheets.append({"properties": {"title": x, "index": i}})

        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        response = self.request(method=method, url=url, params=params, body=body)

        if folderId:
            self.mv(response["spreadsheetId"], folderId)

        return response
    

    def list_videos(self, vids, **kwargs):
        """
        DESCRIPTION:
            Retrieves a list of resources, possibly filtered.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtubepartner"
        \n\n
        PARAMETERS:
            vids: string[]
                Return videos with the given ids.
        """
        method = "youtube:v3.videos.list"

        parts = [
            "contentDetails", "id", "liveStreamingDetails",
            "localizations", "player", "recordingDetails",
            "snippet", "statistics", "status", "topicDetails"
        ]
        parts = kwargs.get("parts", parts)
        
        part = ",".join(parts)
        maxResults=50
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        
        vids = pd.Series(vids)
        raw_vids = list(vids.copy())
        vids = list(vids[vids.fillna("").str.match("([-_A-Za-z0-9]{11})")].unique())
        vids = np.array_split(vids, np.ceil(len(vids) / 50))
        items = []
        for vid in vids:
            params["id"] = ','.join(vid)
            response = self.request(method=method, url=url, params=params, body=body)
            items += response["items"]

        if kwargs.get("raw_output"):
            return {"kind": response["kind"], "items": items}

        cols = {
            "kind": "kind",
            "id": "id",
            "publishedAt": "snippet.publishedAt",
            "channelId": "snippet.channelId",
            "title": "snippet.title",
            "description": "snippet.description",
            "channelTitle": "snippet.channelTitle",
            "categoryId": "snippet.categoryId",
            "tags": "snippet.tags",
            "defaultLanguage": "snippet.defaultLanguage",
            "defaultAudioLanguage": "snippet.defaultAudioLanguage",
            "duration": "contentDetails.duration",
            "viewCount": "statistics.viewCount",
            "likeCount": "statistics.likeCount",
            "favoriteCount": "statistics.favoriteCount",
            "commentCount": "statistics.commentCount",
            "topicIds": "topicDetails.topicIds",
            "topicCategories": "topicDetails.topicCategories"
        }

        result = pd.DataFrame(dict(zip(
            cols.keys(), 
            [jq_lite(items, x) for x in cols.values()]
        )))
        result["viewCount"] = result["viewCount"].astype(float)
        result["likeCount"] = result["likeCount"].astype(float)
        result["favoriteCount"] = result["favoriteCount"].astype(float)
        result["commentCount"] = result["commentCount"].astype(float)

        empty_row = dict(zip(
            list(result.columns), 
            [None for x in range(len(cols))]
        ))
        result = pd.concat([result, pd.DataFrame([empty_row])]).reset_index(drop=True)

        idx = [list(result["id"]).index(x) if x in list(result["id"]) else
            result.shape[0] - 1 for x in raw_vids]
        result = result.iloc[idx]
        result["id"] = raw_vids
        return result.reset_index(drop=True)


    def list_channels(self, cids, **kwargs):
        """
        DESCRIPTION:
            Retrieves a list of resources, possibly filtered.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtubepartner",
            "https://www.googleapis.com/auth/youtubepartner-channel-audit"
        \n\n
        PARAMETERS:
            cids: string[]
                Return the channels with the specified IDs.
        """
        method = "youtube:v3.channels.list"
        parts = [
            "brandingSettings", "contentDetails",
            "contentOwnerDetails", "id", "localizations",
            "snippet", "statistics", "status", "topicDetails"
        ]
        parts = kwargs.get("parts", parts)
        
        part = ",".join(parts)
        maxResults=50
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        
        cids = pd.Series(cids)
        raw_cids = list(cids.copy())
        cids = list(cids[cids.fillna("").str.match("([-_A-Za-z0-9]{11})")].unique())
        cids = np.array_split(cids, np.ceil(len(cids) / 50))
        items = []
        for cid in cids:
            params["id"] = ','.join(cid)
            response = self.request(method=method, url=url, params=params, body=body)
            items += response["items"]

        if kwargs.get("raw_output"):
            return {"kind": response["kind"], "items": items}
        
        cols = {
            "kind": "kind",
            "id": "id",
            "title": "snippet.title",
            "description": "snippet.description",
            "customUrl": "snippet.customUrl",
            "publishedAt": "snippet.publishedAt",
            "country": "snippet.country",
            "uploads": "contentDetails.relatedPlaylists.uploads",
            "viewCount": "statistics.viewCount",
            "subscriberCount": "statistics.subscriberCount",
            "hiddenSubscriberCount": "statistics.hiddenSubscriberCount",
            "videoCount": "statistics.videoCount",
            "topicIds": "topicDetails.topicIds",
            "topicCategories": "topicDetails.topicCategories"
        }

        result = pd.DataFrame(dict(zip(
            cols.keys(), 
            [jq_lite(items, x) for x in cols.values()]
        )))
        result["viewCount"] = result["viewCount"].astype(float)
        result["subscriberCount"] = result["subscriberCount"].astype(float)
        result["videoCount"] = result["videoCount"].astype(float)

        empty_row = dict(zip(
            list(result.columns), 
            [None for x in range(len(cols))]
        ))
        result = pd.concat([result, pd.DataFrame([empty_row])]).reset_index(drop=True)

        idx = [list(result["id"]).index(x) if x in list(result["id"]) else
            result.shape[0] - 1 for x in raw_cids]
        result = result.iloc[idx]
        result["id"] = raw_cids
        return result.reset_index(drop=True)
    

    def list_playlist_items(self, playlistId, parts=None, pageToken=None, **kwargs):
        """
        DESCRIPTION:
            Retrieves a list of resources, possibly filtered.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtubepartner"
        \n\n
        PARAMETERS:
            id: string
                Return the playlist items within the given playlist.
            \n
            full: bool
                If true, all the items (max 20,000) in the playlist will be
                listed.
        """
        method = "youtube:v3.playlistItems.list"
        parts = parts or ["contentDetails", "id", "snippet", "status"]
        
        part = ",".join(parts)
        maxResults=50
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        response = self.request(method=method, url=url, params=params, body=body)
        return response


    def k_vid_before_date(self, playlistId, date, k, include=False, **kwargs):
        """
        Fetch k videos from a playlist (usually channel uploads) before a specific date. 

        date: "YYYY-MM-DDTHH:mm:ssZ"
        """
        if not include:
            d = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
            d = d - timedelta(seconds=1)
            date = d.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        cum_k = 0
        nextPageToken = None
        items = []
        while cum_k < k:
            response = self.list_playlist_items(playlistId, pageToken=nextPageToken)
            items = items + response["items"]
            items_dates = [x["contentDetails"]["videoPublishedAt"] for x in items]
            nextPageToken = response.get("nextPageToken")
            cum_k = sum([x <= date for x in items_dates]) if nextPageToken else k

        cols = {
            "id": "id",
            "channelId": "snippet.channelId",
            "videoId": "contentDetails.videoId",
            "publishedAt": "contentDetails.videoPublishedAt",
            "title": "snippet.title",
            "description": "snippet.description",
            "channelTitle": "snippet.channelTitle"
        }

        result = pd.DataFrame(dict(zip(
            cols.keys(), 
            [jq_lite(items, x) for x in cols.values()]
        )))

        result = result[result["publishedAt"] < date].sort_values(
            "publishedAt", ascending=False
        ).head(k).reset_index(drop=True)

        return result


    def list_gdrive_files(self, q, fields=None, corpora="allDrives", 
                          includeItemsFromAllDrives=True, supportsAllDrives=True, 
                          pageSize=1000, **kwargs):
        """
        DESCRIPTION:
            Lists files in a specific folder (not nested).
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.appdata",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.metadata",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
            "https://www.googleapis.com/auth/drive.photos.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        \n\n
        PARAMETERS:
            fields: string[]
                    Selector specifying which fields to include in a partial
                    response.
            \n
            corpora: string
                    Groupings of files to which the query applies. Supported 
                    groupings are: 'user' (files created by, opened by, or shared 
                    directly with the user), 'drive' (files in the specified 
                    shared drive as indicated by the 'driveId'), 'domain' 
                    (files shared to the user's domain), and 'allDrives' 
                    (A combination of 'user' and 'drive' for all drives where 
                    the user is a member). When able, use 'user' or 'drive', 
                    instead of 'allDrives', for efficiency.
            \n
            includeItemsFromAllDrives: bool
                    Whether both My Drive and shared drive items should be 
                    included in results.
            \n
            supportsAllDrives: bool
                    Whether the requesting application supports both My Drives 
                    and shared drives.
        """
        method = "drive:v3.files.list"
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        if fields:
            params["fields"] = fields
        response = self.request(method=method, url=url, params=params, body=body)
        return response


    def find(self, q, fields=None, iter=10, **kwargs):
        """
        Search in Google Drive via `q`. 
        
        See more from 
        https://developers.google.com/drive/api/guides/search-files#examples
        """
        fields = fields or [
            "driveId", "id", "name", "mimeType", "createdTime", 
            "modifiedTime", "size", "md5Checksum", "owners(emailAddress)", "trashed"
        ]

        fields = "files(" + ','.join(fields) + "),nextPageToken"
        args = {"q": q, "fields": fields, **kwargs}

        files = []
        nextPageToken = None 
        n = 0
        while (nextPageToken is not False) and n < iter:
            n += 1
            args["pageToken"] = nextPageToken
            response = self.list_gdrive_files(**args)
            files = files + response["files"]
            nextPageToken = response.get("nextPageToken", False)
        
        response["files"] = files

        if kwargs.get("raw_output"):
            return response
        
        return pd.DataFrame(files)


    def ls(self, folderId, fields=None, show_trashed=False, iter=10, **kwargs):
        """
        List files (and folders) in a folder
        """
        q="'" + folderId + "' in parents"
        if not show_trashed:
            q = f"({q}) and trashed = false"
        response = self.find(q, fields, iter, **kwargs)
        return response

    def cp(self, fileId, name=None, folderId=None, fields=None, **kwargs):
        """
        Copy a file 
        """
        method = "drive:v3.files.copy"
        supportsAllDrives = kwargs.get("supportsAllDrives", True)
        if folderId:
            parents = [folderId]
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        fields = fields or [
            "driveId", "id", "name", "mimeType", "createdTime", "modifiedTime", "size",
            "md5Checksum", "owners(emailAddress)", "parents"
        ]
        fields = ','.join(fields)
        params["fields"] = fields
        response = self.request(method=method, url=url, params=params, body=body)
        return response
    
    def findone(self, fileId, fields=None, **kwargs):
        """
        DESCRIPTION:
            Gets a file's metadata or content by ID.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.appdata",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.metadata",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
            "https://www.googleapis.com/auth/drive.photos.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        \n\n
        PARAMETERS:
            fileId: string
                    The ID of the file.
            \n
            fields: string[]
                    Selector specifying which fields to include in a partial
                    response.
        """
        method = "drive:v3.files.get"
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        fields = fields or [
            "driveId", "id", "name", "mimeType", "createdTime", "modifiedTime", "size",
            "md5Checksum", "owners(emailAddress)", "parents"
        ]
        fields = ','.join(fields)
        params["fields"] = fields
        response = self.request(method=method, url=url, params=params, body=body)
        return response


    def rm(self, fileId, **kwargs):
        """
        DESCRIPTION:
            Permanently deletes a file owned by the user without moving it to the
            trash. If the file belongs to a shared drive the user must be an
            organizer on the parent. If the target is a folder, all descendants
            owned by the user are also deleted.
        \n\n
        SCOPES:
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.appdata",
            "https://www.googleapis.com/auth/drive.file"
        \n\n
        PARAMETERS:
            fileId: string
                    The ID of the file.
        """
        method = "drive:v3.files.delete"
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        return self.request(method=method, url=url, params=params, body=body)


    def credate_gdrive_files(self, fileId=None, uploadType=None, fields=None, **kwargs):
        """
        Generic API call to create or update a file
        """
        method = "drive:v3.files.update" if fileId else "drive:v3.files.create"
        fields = fields or [
            "driveId", "id", "name", "mimeType", "createdTime", "size",
            "md5Checksum", "parents"
        ]
        fields = ','.join(fields)
        build_args = locals()
        del build_args["self"]
        service_doc, method_doc, method, url, params, body = self.build_params(**build_args)
        params["fields"] = fields
        if kwargs.get("files"):
            url = "https://www.googleapis.com/upload/drive/v3/files"
            url = url + f"/{fileId}" if fileId else url
            params["uploadType"] = uploadType
            body = None
        return self.request(method=method, url=url, params=params, body=body, files=kwargs.get("files"))

    def ln(self, targetId, name=None, folderId=None, fields=None, **kwargs):
        """
        Create a shortcut to a file
        """
        folderId = folderId or "root"
        shortcutDetails = {
            "targetId": targetId
        }
        args = {
            "shortcutDetails": shortcutDetails,
            'mimeType': 'application/vnd.google-apps.shortcut',
            "name": name,
            "parents": [folderId] if type(folderId) is str else folderId,
            "fields": fields,
            **kwargs
        }
        response = self.credate_gdrive_files(**args)
        return response

    def mkdir(self, folderName, folderId=None, fields=None, **kwargs):
        """
        Create a new folder
        """
        folderId = folderId or "root"
        args = {
            "name": folderName,
            "parents": [folderId] if type(folderId) is str else folderId,
            "fields": fields,
            "mimeType": "application/vnd.google-apps.folder",
            **kwargs
        }
        return self.credate_gdrive_files(**args)
    
    def mv(self, fileId, folderId, fields=None, **kwargs):
        """
        Move a file
        """
        args = {
            "fileId": fileId,
            "removeParents": self.findone(fileId, ["parents"])["parents"],
            "addParents": folderId,
            "fields": fields,
            **kwargs
        }
        return self.credate_gdrive_files(**args)
    
    def upload_file(self, fpath, name=None, fileId=None, folderId=None, mimeType=None, 
                    metadata=None, fields=None, **kwargs):
        """
        Upload or update a file
        """
        metadata = metadata or dict()
        folderId = folderId or "root"
        folderId = [folderId] if type(folderId) is str else folderId
        uploadType = "multipart"
        
        if type(fpath) is str and mimeType is None:
            _, ext = os.path.splitext(fpath)
            try:
                mimeType = mimetypes.types_map[ext]
            except Exception:
                mimeType = None

        if type(fpath) is str:
            name = name or os.path.split(fpath)[-1]
            with open(fpath, "rb") as f:
                fpath = f.read()
        elif type(fpath) is io.BytesIO:
            fpath = fpath.getvalue()

        if "name" not in metadata:
            metadata["name"] = name
        if mimeType and "mimeType" not in metadata:
            metadata["mimeType"] = mimeType

        if folderId:
            if fileId is None:
                if "parents" not in metadata:
                    metadata["parents"] = folderId
            else:
                metadata["removeParents"] = self.findone(fileId, ["parents"])["parents"]
                metadata["addParents"] = folderId
        
        files = {
            "data": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
            "file": fpath
        }

        args = {
            "fields": fields,
            "uploadType": uploadType,
            "files": files,
            **kwargs
        }

        if fileId:
            args["fileId"] = fileId

        return self.credate_gdrive_files(**args)
    

    def download_file(self, fileId, path=None, **kwargs):
        """
        Download a file
        """
        url = f"https://www.googleapis.com/drive/v3/files/{fileId}?alt=media&source=downloadUrl"
        response = request("GET", url, headers=self.headers)

        if not response.ok:
            print(response.content.decode("utf-8"))
            response.raise_for_status()
        
        if path:
            with open(path, "wb") as f:
                f.write(response.content)
                return None 
        
        file = io.BytesIO(response.content)
        return file
    

    def gdrive_about(self, fields=None, **kwargs):
        """
        Gets information about the user, the user's Drive, and system capabilities.
        Method: drive:v3.about
        """
        url = "https://www.googleapis.com/drive/v3/about"
        fields = fields or [
            "kind", "user(displayName,permissionId,emailAddress)",
            "storageQuota", "maxUploadSize", "canCreateTeamDrives",
            "canCreateDrives"
        ]
        params = {
            "fields": ",".join(fields)
        }
        response = self.request(method="GET", url=url, params=params)
        return response


def yt_vid_from_vurl(x):
    """
    Known type:
        urls = [
            "http://www.youtube.com/watch?v=-wtIMTCHWuI",
            "http://www.youtube.com/v/-wtIMTCHWuI?version=3&autohide=1",
            "http://youtu.be/-wtIMTCHWuI",
            "http://www.youtube.com/oembed?url=http%3A//www.youtube.com/watch?v%3D-wtIMTCHWuI&format=json",
            "http://www.youtube.com/attribution_link?a=JdfC0C9V6ZI&u=%2Fwatch%3Fv%3DEhxJLojIE_o%26feature%3Dshare",
            "https://www.youtube.com/attribution_link?a=8g8kPrPIi-ecwIsS&u=/watch%3Fv%3DyZv2daTWRZU%26feature%3Dem-uploademail",
            "https://www.youtube.com/watch?v=yZv2daTWRZU&feature=em-uploademail",
            "https://www.youtube.com/watch?v=0zM3nApSvMg&feature=feedrec_grec_index",
            "https://www.youtube.com/user/IngridMichaelsonVEVO#p/a/u/1/QdK8U-VIH_o",
            "https://www.youtube.com/v/0zM3nApSvMg?fs=1&amp;hl=en_US&amp;rel=0",
            "https://www.youtube.com/watch?v=0zM3nApSvMg#t=0m10s",
            "https://www.youtube.com/embed/0zM3nApSvMg?rel=0",
            "https://www.youtube-nocookie.com/embed/up_lNV-yoK4?rel=0",
            "https://www.youtube-nocookie.com/embed/up_lNV-yoK4?rel=0",
            "http://www.youtube.com/user/Scobleizer#p/u/1/1p3vcRhsYGo",
            "http://www.youtube.com/watch?v=cKZDdG9FTKY&feature=channel",
            "http://www.youtube.com/watch?v=yZ-K7nCVnBI&playnext_from=TL&videos=osPknwzXEas&feature=sub",
            "http://www.youtube.com/ytscreeningroom?v=NRHVzbJVx8I",
            "http://www.youtube.com/watch?v=6dwqZw0j_jY&feature=youtu.be",
            "http://www.youtube.com/user/Scobleizer#p/u/1/1p3vcRhsYGo?rel=0",
            "http://www.youtube.com/embed/nas1rJpm7wY?rel=0",
            "https://www.youtube.com/watch?v=peFZbP64dsU",
            "http://youtube.com/v/dQw4w9WgXcQ?feature=youtube_gdata_player",
            "http://youtube.com/?v=dQw4w9WgXcQ&feature=youtube_gdata_player",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtube_gdata_player",
            "http://youtube.com/?vi=dQw4w9WgXcQ&feature=youtube_gdata_player",
            "http://youtube.com/watch?v=dQw4w9WgXcQ&feature=youtube_gdata_player",
            "http://youtube.com/watch?vi=dQw4w9WgXcQ&feature=youtube_gdata_player",
            "http://youtube.com/vi/dQw4w9WgXcQ?feature=youtube_gdata_player",
            "http://youtu.be/dQw4w9WgXcQ?feature=youtube_gdata_player",
            "http://www.youtube.com/user/SilkRoadTheatre#p/a/u/2/6dwqZw0j_jY",
            "https://www.youtube.com/watch?v=ishbTyLs6ps&list=PLGup6kBfcU7Le5laEaCLgTKtlDcxMqGxZ&index=106&shuffle=2655",
            "http://www.youtube.com/v/0zM3nApSvMg?fs=1&hl=en_US&rel=0",
            "http://www.youtube.com/watch?v=0zM3nApSvMg&feature=feedrec_grec_index",
            "http://www.youtube.com/watch?v=0zM3nApSvMg#t=0m10s",
            "http://www.youtube.com/embed/dQw4w9WgXcQ",
            "http://www.youtube.com/v/dQw4w9WgXcQ",
            "http://www.youtube.com/e/dQw4w9WgXcQ",
            "http://www.youtube.com/?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?feature=player_embedded&v=dQw4w9WgXcQ",
            "http://www.youtube.com/?feature=player_embedded&v=dQw4w9WgXcQ",
            "http://www.youtube.com/user/IngridMichaelsonVEVO#p/u/11/KdwsulMb8EQ",
            "http://www.youtube-nocookie.com/v/6L3ZvIMwZFM?version=3&hl=en_US&rel=0",
            "http://www.youtube.com/user/dreamtheater#p/u/1/oTJRivZTMLs",
            "https://youtu.be/oTJRivZTMLs?list=PLToa5JuFMsXTNkrLJbRlB--76IAOjRM9b",
            "http://www.youtube.com/watch?v=oTJRivZTMLs&feature=youtu.be",
            "http://youtu.be/oTJRivZTMLs&feature=channel",
            "http://www.youtube.com/ytscreeningroom?v=oTJRivZTMLs",
            "http://www.youtube.com/embed/oTJRivZTMLs?rel=0",
            "http://youtube.com/vi/oTJRivZTMLs&feature=channel",
            "http://youtube.com/?v=oTJRivZTMLs&feature=channel",
            "http://youtube.com/?feature=channel&v=oTJRivZTMLs",
            "http://youtube.com/?vi=oTJRivZTMLs&feature=channel",
            "http://youtube.com/watch?v=oTJRivZTMLs&feature=channel",
            "http://youtube.com/watch?vi=oTJRivZTMLs&feature=channel",
            "https://www.youtube.com/shorts/IvVaIW1bXQ0"
        ]

    Reference:
        https://gist.github.com/rodrigoborgesdeoliveira/987683cfbfcc8d800192da1e73adc486
    """
    x = pd.Series(x)
    output = x.str.extract("(?:youtube(?:-nocookie)*\.com.*(?:vi*=|vi*%3D|/(?:embed|vi*|e|shorts|u/\d+)/)|youtu\.be/)([A-z0-9-_]{11})(?:[%#?&/\s]|$)")[0]
    output = list(output.where(output.notnull(), [None]))
    output = output[0] if len(output) == 1 else output
    return output


def yt_cid_from_curl(urls, headers=None, cookies=None):
    """
    Known type: "c", "channel", and "user"
    https://support.google.com/youtube/answer/6180214?hl=en-GB

    urls = [
        "https://www.youtube.com/channel/UCO22Xm0wVcgE1x9AwMCla1Q/videos",
        "https://www.youtube.com/AndySterkowitz/",
        "https://www.youtube.com/c/Coreyms/",
        "https://www.youtube.com/user/THiNKmediaTV/"
    ]
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    urls = [urls] if type(urls) is str else urls
    cookies = cookies or {"CONSENT": "YES+yt.463627267.en-GB+FX+553"} 
    if headers is None:
        headers = {
            'accept': '*/*', 
            'accept-encoding': 'gzip, deflate', 
            'connection': 'keep-alive', 
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5400.117 Safari/537.36'
        }
    channel_id_re = re.compile(".*youtube\\.com/channel/([-_0-9A-z]{24}).*")
    external_id_re = re.compile('[\w\W]*"(?:externalChannelId|externalId)":"([A-z0-9-_]{24})"')
    sem = asyncio.Semaphore(50)

    async def fetch_channel_id(client, url):
        async with sem:
            result = channel_id_re.match(url)
            if result:
                return result.group(1)
            
            client.cookies = cookies
            client.headers = headers
            response = await client.get(url, follow_redirects=True)

            if not response.is_success:
                url = url.replace("/c/", "/")
                response = await client.get(url, follow_redirects=True)
            
            result = external_id_re.match(response.text)
            if result:
                return result.group(1)
            return None

    async def main():
        async with httpx.AsyncClient() as client:
            client.timeout = 10
            tasks = []
            for url in urls:
                tasks.append(asyncio.create_task(fetch_channel_id(client, url)))
            
            result = await asyncio.gather(*tasks)
        return result
    
    result = asyncio.run(main())
    result = result[0] if len(urls) == 1 else result
    loop.close()
    return result

