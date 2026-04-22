import requests
import json
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import io

# Extract variables once
files_list = client_data.get("files", [])
variables = client_data.get("variables", {})
filename = variables.get("Filename", "downloaded_file")
folder_id = variables.get("FolderId", "")
party_name = variables.get("PartyName", "")

# Early validation with combined check
if not files_list:
    output = "No files are available to download"
elif not party_name:
    output = "PartyName variable is required but not provided"
elif not folder_id:
    output = "FolderId variable is required but not provided"
else:
    try:
        if 'credentials' not in globals() or not credentials:
            output = "Credentials not available"
        else:
            google_creds_info = None
            impersonate_user = None

            if isinstance(credentials, dict):
                if 'google_drive_' in credentials:
                    if isinstance(credentials['google_drive_'], dict):
                        if 'data' in credentials['google_drive_']:
                            google_creds_info = credentials['google_drive_']['data'].get('serviceAccountCredentials')
                            impersonate_user = credentials['google_drive_']['data'].get('impersonateUser')
                        else:
                            google_creds_info = credentials['google_drive_'].get('serviceAccountCredentials')
                            impersonate_user = credentials['google_drive_'].get('impersonateUser')
                    else:
                        try:
                            parsed_creds = json.loads(credentials['google_drive_'])
                            google_creds_info = parsed_creds.get('serviceAccountCredentials')
                            impersonate_user = parsed_creds.get('impersonateUser')
                        except:
                            google_creds_info = None

            if not google_creds_info:
                output = "Google Service Account credentials not found or improperly formatted"
            else:
                if isinstance(google_creds_info, str):
                    try:
                        google_creds_info = json.loads(google_creds_info)
                    except json.JSONDecodeError:
                        output = "Invalid JSON format in service account credentials"
                        raise Exception("Invalid credential format")

                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
                missing_fields = [field for field in required_fields if field not in google_creds_info]

                if missing_fields:
                    output = f"Service account credentials missing required fields: {', '.join(missing_fields)}"
                    raise Exception("Incomplete service account credentials")

                if google_creds_info.get('type') != 'service_account':
                    output = "Credentials must be for a service account, not a client application"
                    raise Exception("Invalid credential type")

                scopes = ['https://www.googleapis.com/auth/drive']

                google_creds = service_account.Credentials.from_service_account_info(
                    google_creds_info,
                    scopes=scopes
                )

                if impersonate_user:
                    try:
                        google_creds = google_creds.with_subject(impersonate_user)
                    except Exception as e:
                        output = f"Failed to impersonate user {impersonate_user}: {str(e)}"
                        raise Exception("Impersonation failed")

                drive_service = build('drive', 'v3', credentials=google_creds)

                # Search for existing folder matching PartyName under the target FolderId
                target_folder_id = None
                search_query = (
                    f"name='{party_name}' and "
                    f"mimeType='application/vnd.google-apps.folder' and "
                    f"'{folder_id}' in parents and "
                    f"trashed=false"
                )

                folder_search_results = drive_service.files().list(
                    q=search_query,
                    fields='files(id, name)',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                folders = folder_search_results.get('files', [])

                if folders:
                    target_folder_id = folders[0]['id']
                    folder_status = f"Found existing folder '{party_name}' with ID: {target_folder_id}"
                else:
                    folder_metadata = {
                        'name': party_name,
                        'parents': [folder_id],
                        'mimeType': 'application/vnd.google-apps.folder'
                    }

                    created_folder = drive_service.files().create(
                        body=folder_metadata,
                        fields='id,name',
                        supportsAllDrives=True
                    ).execute()

                    target_folder_id = created_folder['id']
                    folder_status = f"Created new folder '{party_name}' with ID: {target_folder_id}"

                # Download file from URL
                file_url = files_list[0]
                file_response = requests.get(file_url, timeout=30)
                file_response.raise_for_status()

                clean_filename = filename.replace(' ', '_')

                # Detect MIME type from extension
                mime_map = {
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.pdf': 'application/pdf',
                    '.txt': 'text/plain',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                }
                ext = os.path.splitext(clean_filename.lower())[1]
                mime_type = mime_map.get(ext, 'application/octet-stream')

                file_metadata = {
                    'name': clean_filename,
                    'parents': [target_folder_id]
                }

                media = MediaIoBaseUpload(
                    io.BytesIO(file_response.content),
                    mimetype=mime_type,
                    resumable=True
                )

                upload_result = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,webViewLink,parents',
                    supportsAllDrives=True
                ).execute()

                output = (
                    f"{folder_status}. "
                    f"Successfully uploaded {clean_filename} to Google Drive "
                    f"in PartyName folder {target_folder_id}. "
                    f"File ID: {upload_result['id']}, "
                    f"View Link: {upload_result.get('webViewLink', 'N/A')}"
                )

    except HttpError as error:
        error_details = f"Status: {error.resp.status}"
        try:
            error_content = json.loads(error.content.decode())
            error_message = error_content.get('error', {}).get('message', 'Unknown error')
            error_details += f", Message: {error_message}"
        except:
            error_details += f", Raw content: {error.content.decode()}"
        output = f"Google Drive API error - {error_details}"
    except requests.RequestException as e:
        output = f"Network error downloading file: {str(e)}"
    except KeyError as e:
        output = f"Missing Google Service Account credential configuration: {str(e)}"
    except Exception as e:
        output = f"Error uploading file to Google Drive: {str(e)}"
