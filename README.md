# Email Decoder

A Python utility for decoding and extracting content from email messages. Supports both raw email format and base64-encoded emails, with automatic detection and comprehensive content extraction.

## Features

- Decode raw email messages and base64-encoded emails
- Extract text and HTML body content
- Extract and save images (inline and attached)
- Extract file attachments
- Save email headers for reference
- Auto-detect email format (raw vs base64)
- Handle JSON files containing email data
- Generate metadata for extracted files
- Comprehensive error handling and logging

## Installation

No additional dependencies required beyond Python's standard library.

## Usage

### Command Line Usage

```bash
# Basic usage with auto-detection
python email_decoder.py email.txt

# Specify output directory
python email_decoder.py email.txt my_output_folder

# Force base64 decoding
python email_decoder.py email_base64.txt --base64

# With custom output directory and base64 mode
python email_decoder.py email_base64.txt my_output --base64
```

### Python Import Usage

```python
from email_decoder import (
    decode_email_from_file,
    extract_email_content,
    decode_base64_email,
    decode_raw_email,
    get_email_summary
)

# Decode from file
text_body, html_body = decode_email_from_file("email.txt", "output_dir")

# Extract from string
text_body, html_body = extract_email_content(email_string, "output_dir")

# Decode base64 email
text_body, html_body = decode_base64_email(base64_string, "output_dir")

# Decode raw email
text_body, html_body = decode_raw_email(raw_email_string, "output_dir")

# Get email summary without extracting files
summary = get_email_summary(email_string)
```

## Functions

### `decode_email_from_file(file_path, output_dir, is_base64)`
Decodes email from a file. Supports JSON files with `raw_email` field.

### `extract_email_content(email_input, output_dir, is_base64)`
Main function that auto-detects email format and extracts content.

### `decode_base64_email(base64_email_string, output_dir)`
Specifically for base64-encoded emails.

### `decode_raw_email(raw_email_string, output_dir)`
For raw email message strings.

### `get_email_summary(email_input, is_base64)`
Returns a summary of email content without extracting files.

## Output Structure

The script creates an output directory containing:

- `body.txt` - Plain text email body
- `body.html` - HTML email body
- `headers.txt` - Email headers
- Images and attachments with original or generated names
- `*_metadata.txt` - Metadata files for images

## Supported Formats

- Raw email messages (.eml, .txt)
- Base64-encoded emails
- JSON files containing email data
- Multipart emails with attachments
- Inline images with Content-ID references

## Error Handling

The script includes comprehensive error handling and will:
- Continue processing other parts if one part fails
- Generate unique filenames to avoid conflicts
- Provide detailed logging of the extraction process
- Handle various character encodings gracefully

## Examples

### Raw Email File
```bash
python email_decoder.py raw_email.eml
```

### Base64 Email
```bash
python email_decoder.py base64_email.txt --base64
```

### JSON Email Data
```bash
python email_decoder.py email_data.json
```

The script will automatically detect the format and extract all available content to the specified output directory.
