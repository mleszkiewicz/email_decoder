import email
from email import policy
import base64
import os
import io
from typing import Tuple, Optional

def decode_base64_email(base64_email_string: str, output_dir: str = "decoded_email_content") -> Tuple[Optional[str], Optional[str]]:
    """
    Decodes a base64 encoded email string and extracts its content.
    
    Args:
        base64_email_string (str): The base64 encoded email string.
        output_dir (str): The directory where extracted content will be saved.
        
    Returns:
        Tuple[Optional[str], Optional[str]]: (text_body, html_body)
    """
    try:
        # Decode the base64 string to get the raw email
        raw_email_bytes = base64.b64decode(base64_email_string)
        raw_email_string = raw_email_bytes.decode('utf-8', errors='replace')
        
        return decode_raw_email(raw_email_string, output_dir)
    except Exception as e:
        print(f"Error decoding base64 email: {e}")
        return None, None


def decode_raw_email(raw_email_string: str, output_dir: str = "decoded_email_content") -> Tuple[Optional[str], Optional[str]]:
    """
    Decodes a raw email message string, extracts its parts (text, HTML, images, attachments),
    and saves them to the specified output directory.

    Args:
        raw_email_string (str): The complete raw email message as a string.
        output_dir (str): The directory where extracted content will be saved.
        
    Returns:
        Tuple[Optional[str], Optional[str]]: (text_body, html_body)
    """
    try:
        # Parse the raw email string into an email.message.Message object
        # Using policy.default ensures a robust parsing experience.
        msg = email.message_from_string(raw_email_string, policy=policy.default)

        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f"Output directory created/verified: {os.path.abspath(output_dir)}")

        html_body = None
        text_body = None
        
        # Keep track of extracted files to avoid overwriting if names collide
        extracted_files = set()
        
        # Debug information
        print(f"Email has {len(list(msg.walk()))} parts to process")
        
        # Walk through all parts of the email message
        for part_num, part in enumerate(msg.walk()):
            print(f"\nProcessing part {part_num + 1}:")
            print(f"  Content-Type: {part.get_content_type()}")
            print(f"  Filename: {part.get_filename()}")
            print(f"  Content-Disposition: {part.get('Content-Disposition')}")
            print(f"  Content-ID: {part.get('Content-ID')}")
            print(f"  Is multipart: {part.is_multipart()}")
            
            # Skip the multipart container itself, as it doesn't contain direct content
            if part.is_multipart():
                print(f"  -> Skipping multipart container")
                continue

            # Get content type and filename
            content_type = part.get_content_type()
            filename = part.get_filename()
            content_disposition = part.get('Content-Disposition')
            
            # Get the payload. decode=True automatically decodes common encodings like Base64.
            try:
                payload = part.get_payload(decode=True)
                print(f"  -> Payload size: {len(payload) if payload else 0} bytes")
            except Exception as e:
                print(f"  -> Error decoding payload for part {content_type} (filename: {filename}): {e}")
                continue

            # Handle text parts (plain and HTML)
            if content_type == 'text/plain':
                try:
                    # Decode text content using the specified charset or default to utf-8
                    text_body = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                    file_path = os.path.join(output_dir, "body.txt")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(text_body)
                    print(f"Extracted plain text body to: {file_path}")
                except Exception as e:
                    print(f"Error decoding plain text body: {e}")

            elif content_type == 'text/html':
                try:
                    # Decode HTML content
                    html_body = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                    file_path = os.path.join(output_dir, "body.html")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html_body)
                    print(f"Extracted HTML body to: {file_path}")
                except Exception as e:
                    print(f"Error decoding HTML body: {e}")

            # Handle image attachments or embedded images - enhanced detection
            elif (content_type.startswith('image/') or 
                  (filename and any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'])) or
                  (content_disposition and 'attachment' in content_disposition.lower()) or
                  part.get('Content-ID')):
                
                print(f"  -> Detected as image/attachment")
                
                if payload and len(payload) > 0:
                    # Determine filename for the image
                    if filename:
                        # Use provided filename for attachments
                        image_name = filename
                        print(f"  -> Using provided filename: {image_name}")
                    else:
                        # For embedded images, try Content-ID, otherwise generate a name
                        cid = part.get('Content-ID')
                        if cid:
                            # Clean Content-ID to make it a valid filename
                            clean_cid = cid.strip('<>').replace('@', '_at_').replace('.', '_').replace('/', '_')
                            # Get file extension from content type
                            ext = content_type.split('/')[-1] if '/' in content_type else 'bin'
                            image_name = f"{clean_cid}.{ext}"
                            print(f"  -> Generated name from Content-ID: {image_name}")
                        else:
                            # Generate a unique name if no filename or Content-ID
                            ext = content_type.split('/')[-1] if '/' in content_type else 'bin'
                            image_name = f"image_{part_num + 1}.{ext}"
                            print(f"  -> Generated generic name: {image_name}")
                    
                    # Ensure filename is unique in the output directory
                    original_image_name = image_name
                    counter = 1
                    while image_name in extracted_files:
                        name_parts = os.path.splitext(original_image_name)
                        image_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                        counter += 1

                    image_path = os.path.join(output_dir, image_name)
                    try:
                        with open(image_path, 'wb') as f:
                            f.write(payload)
                        extracted_files.add(image_name)
                        print(f"  -> ✓ Successfully extracted image: {image_name} ({len(payload)} bytes)")
                        
                        # Also save image metadata for reference
                        metadata = {
                            'content_type': content_type,
                            'original_filename': filename,
                            'content_id': part.get('Content-ID'),
                            'content_disposition': part.get('Content-Disposition'),
                            'size_bytes': len(payload),
                            'part_number': part_num + 1
                        }
                        
                        metadata_path = os.path.join(output_dir, f"{os.path.splitext(image_name)[0]}_metadata.txt")
                        with open(metadata_path, 'w', encoding='utf-8') as f:
                            for key, value in metadata.items():
                                if value is not None:
                                    f.write(f"{key}: {value}\n")
                        
                    except Exception as e:
                        print(f"  -> ✗ Error saving image {image_name}: {e}")
                else:
                    print(f"  -> ✗ Skipping empty or no payload: {content_type} (filename: {filename})")

            # Handle other types of attachments
            elif filename or (content_disposition and 'attachment' in content_disposition.lower()):
                print(f"  -> Detected as general attachment")
                
                if payload and len(payload) > 0:
                    # Use filename or generate one
                    attachment_name = filename or f"attachment_{part_num + 1}"
                    
                    # Ensure filename is unique in the output directory
                    original_filename = attachment_name
                    counter = 1
                    while attachment_name in extracted_files:
                        name_parts = os.path.splitext(original_filename)
                        attachment_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                        counter += 1

                    attachment_path = os.path.join(output_dir, attachment_name)
                    try:
                        with open(attachment_path, 'wb') as f:
                            f.write(payload)
                        extracted_files.add(attachment_name)
                        print(f"  -> ✓ Successfully extracted attachment: {attachment_name} ({len(payload)} bytes)")
                    except Exception as e:
                        print(f"  -> ✗ Error saving attachment {attachment_name}: {e}")
                else:
                    print(f"  -> ✗ Skipping empty attachment: {content_type} (filename: {filename})")
            else:
                # This part has no filename and is not text/html/image, might be unhandled content
                print(f"  -> Unhandled part: Content-Type: {content_type}, Size: {len(payload) if payload else 0} bytes")
                # Still try to extract if it has substantial content
                if payload and len(payload) > 100:  # Only extract if substantial content
                    unknown_filename = f"unknown_part_{part_num + 1}.bin"
                    unknown_path = os.path.join(output_dir, unknown_filename)
                    try:
                        with open(unknown_path, 'wb') as f:
                            f.write(payload)
                        print(f"  -> ✓ Extracted unknown content as: {unknown_filename}")
                    except Exception as e:
                        print(f"  -> ✗ Error saving unknown content: {e}")

        # Save email headers for reference
        headers_path = os.path.join(output_dir, "headers.txt")
        with open(headers_path, 'w', encoding='utf-8') as f:
            f.write("Email Headers:\n")
            f.write("=" * 50 + "\n")
            for key, value in msg.items():
                f.write(f"{key}: {value}\n")
        
        print(f"\n" + "="*60)
        print(f"Email decoding complete!")
        print(f"Total files extracted: {len(extracted_files)}")
        print(f"Output directory: {os.path.abspath(output_dir)}")
        print(f"Files created: {', '.join(sorted(extracted_files)) if extracted_files else 'None'}")
        print("="*60)
        return text_body, html_body

    except Exception as e:
        print(f"\n✗ An error occurred during email decoding: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def extract_email_content(email_input: str, output_dir: str = "decoded_email_content", is_base64: bool = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Convenience function to extract email content from either raw email or base64 encoded email.
    
    Args:
        email_input (str): Either raw email string or base64 encoded email string.
        output_dir (str): The directory where extracted content will be saved.
        is_base64 (bool): If True, treats input as base64. If False, treats as raw email.
                         If None, attempts to auto-detect.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: (text_body, html_body)
    """
    if is_base64 is None:
        # Auto-detect if input is base64 encoded
        try:
            # Try to decode as base64 and see if it looks like an email
            decoded = base64.b64decode(email_input).decode('utf-8', errors='replace')
            if 'From:' in decoded or 'To:' in decoded or 'Subject:' in decoded:
                is_base64 = True
            else:
                is_base64 = False
        except:
            is_base64 = False
    
    if is_base64:
        return decode_base64_email(email_input, output_dir)
    else:
        return decode_raw_email(email_input, output_dir)


def get_email_summary(email_input: str, is_base64: bool = None) -> dict:
    """
    Get a summary of email content without extracting files.
    
    Args:
        email_input (str): Either raw email string or base64 encoded email string.
        is_base64 (bool): If True, treats input as base64. If None, attempts to auto-detect.
    
    Returns:
        dict: Summary containing headers, body info, and attachment info.
    """
    try:
        if is_base64 is None:
            # Auto-detect if input is base64 encoded
            try:
                decoded = base64.b64decode(email_input).decode('utf-8', errors='replace')
                if 'From:' in decoded or 'To:' in decoded or 'Subject:' in decoded:
                    raw_email = decoded
                else:
                    raw_email = email_input
            except:
                raw_email = email_input
        elif is_base64:
            raw_email = base64.b64decode(email_input).decode('utf-8', errors='replace')
        else:
            raw_email = email_input
        
        msg = email.message_from_string(raw_email, policy=policy.default)
        
        summary = {
            'headers': {
                'from': msg.get('From'),
                'to': msg.get('To'),
                'subject': msg.get('Subject'),
                'date': msg.get('Date'),
                'message_id': msg.get('Message-ID')
            },
            'body': {
                'has_text': False,
                'has_html': False,
                'text_preview': None,
                'html_preview': None
            },
            'attachments': {
                'count': 0,
                'images': 0,
                'files': []
            }
        }
        
        for part in msg.walk():
            if part.is_multipart():
                continue
            
            content_type = part.get_content_type()
            filename = part.get_filename()
            
            if content_type == 'text/plain':
                summary['body']['has_text'] = True
                try:
                    payload = part.get_payload(decode=True)
                    text_content = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                    summary['body']['text_preview'] = text_content[:200] + '...' if len(text_content) > 200 else text_content
                except:
                    pass
            
            elif content_type == 'text/html':
                summary['body']['has_html'] = True
                try:
                    payload = part.get_payload(decode=True)
                    html_content = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
                    summary['body']['html_preview'] = html_content[:200] + '...' if len(html_content) > 200 else html_content
                except:
                    pass
            
            elif content_type.startswith('image/'):
                summary['attachments']['images'] += 1
                summary['attachments']['count'] += 1
                summary['attachments']['files'].append({
                    'type': 'image',
                    'content_type': content_type,
                    'filename': filename,
                    'content_id': part.get('Content-ID')
                })
            
            elif filename:
                summary['attachments']['count'] += 1
                summary['attachments']['files'].append({
                    'type': 'attachment',
                    'content_type': content_type,
                    'filename': filename
                })
        
        return summary
        
    except Exception as e:
        return {'error': str(e)}


def decode_email_from_file(file_path: str, output_dir: str = "decoded_email_content", is_base64: bool = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Convenience function to decode email from a file.
    
    Args:
        file_path (str): Path to the file containing the email (raw or base64).
        output_dir (str): The directory where extracted content will be saved.
        is_base64 (bool): If True, treats file content as base64. If None, attempts to auto-detect.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: (text_body, html_body)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read().strip()
        
        # Check if this is JSON containing email data
        if file_content.startswith('{') and '"raw_email"' in file_content:
            import json
            try:
                data = json.loads(file_content)
                if 'raw_email' in data:
                    print("✓ Detected JSON format with raw_email field")
                    email_content = data['raw_email']
                    return extract_email_content(email_content, output_dir, False)  # Raw email from JSON
                elif 'payload' in data and 'raw_email' in str(data['payload']):
                    print("✓ Detected JSON format with raw_email in payload")
                    email_content = data['payload']['raw_email']
                    return extract_email_content(email_content, output_dir, False)  # Raw email from JSON
            except json.JSONDecodeError:
                print("⚠ JSON parsing failed, treating as raw email")
        
        # Fallback to treating as raw email or base64
        return extract_email_content(file_content, output_dir, is_base64)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None, None


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python email_decoder.py <email_file_path> [output_dir]")
        print("  python email_decoder.py <email_file_path> [output_dir] --base64")
        print()
        print("Examples:")
        print("  python email_decoder.py email.txt")
        print("  python email_decoder.py email_base64.txt my_output --base64")
        print()
        print("Functions available for import:")
        print("  - decode_email_from_file(file_path, output_dir)")
        print("  - extract_email_content(email_string, output_dir)")
        print("  - decode_base64_email(base64_string, output_dir)")
        print("  - decode_raw_email(raw_email_string, output_dir)")
        print("  - get_email_summary(email_string)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "decoded_email_content"
    is_base64 = '--base64' in sys.argv
    
    print(f"Processing email from: {file_path}")
    print(f"Output directory: {output_dir}")
    print(f"Base64 mode: {'Yes' if is_base64 else 'Auto-detect'}")
    print("-" * 50)
    
    text_body, html_body = decode_email_from_file(file_path, output_dir, is_base64 if is_base64 else None)
    
    if text_body or html_body:
        print(f"\nExtraction completed successfully!")
        print(f"Check the '{output_dir}' directory for all extracted files.")
    else:
        print("\nExtraction failed. Please check the file and try again.")

