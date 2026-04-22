# Google Drive Upload — Party Name Folder Routing

Uploads a file to Google Drive into a subfolder named after a third-party (`PartyName`). The target parent folder is determined by `FolderId` (typically set by a prior classification step). If a subfolder matching `PartyName` already exists under that parent, the file is uploaded there; otherwise a new subfolder is created first.

## Expected Inputs

This snippet runs inside an automation context where two objects are pre-populated:

| Object | Key | Description |
|---|---|---|
| `client_data` | `files` | List of one or more file URLs to upload (only the first is used) |
| `client_data` | `variables.Filename` | Desired filename for the uploaded file |
| `client_data` | `variables.FolderId` | Google Drive ID of the classification-determined parent folder |
| `client_data` | `variables.PartyName` | Third-party name used as the subfolder name |
| `credentials` | `google_drive_` | Google Service Account credentials (see Credential Format below) |

## Credential Format

The `credentials['google_drive_']` value is expected to be a dict (or JSON string) with two keys:

```json
{
  "serviceAccountCredentials": { ... },
  "impersonateUser": "user@domain.com"
}
```

`serviceAccountCredentials` must be a valid Google service account JSON with at minimum: `type`, `project_id`, `private_key_id`, `private_key`, `client_email`, `client_id`.

`impersonateUser` is optional. When provided, the service account will act on behalf of that user via domain-wide delegation.

## Logic Flow

```
client_data received
  └─ Validate: files_list, PartyName, FolderId present
  └─ Parse & validate service account credentials
  └─ Build Drive v3 service (with optional impersonation)
  └─ Search for existing folder: name=PartyName, parent=FolderId
        ├─ Found  → use existing folder ID
        └─ Not found → create new folder under FolderId
  └─ Download file from files_list[0]
  └─ Detect MIME type from file extension
  └─ Upload file into target subfolder
  └─ Set output string with folder status + upload result
```

## Output

`output` is set to a string in all cases:

- **Success**: confirms folder found/created, filename, file ID, and a web view link.
- **Error**: descriptive message covering credential issues, API errors, network failures, or missing fields.

## Supported MIME Types

| Extension | MIME Type |
|---|---|
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `.pdf` | `application/pdf` |
| `.txt` | `text/plain` |
| `.jpg` / `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| other | `application/octet-stream` |

## Dependencies

```
google-api-python-client
google-auth
requests
```
