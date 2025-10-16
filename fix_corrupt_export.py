import re

# Read file
with open(r'c:\VCC\VPB\vpb\services\export_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix corrupted lines - remove the backslash escapes
content = content.replace(r'getattr(document, \ document_id\, str(id(document)))', 'getattr(document, "document_id", str(id(document)))')

# Also fix the f-string version
content = content.replace(r'f\'Definitions_{getattr(document, \ document_id\, str(id(document)))}\'', 'f"Definitions_{getattr(document, \\\"document_id\\\", str(id(document)))}"')
content = content.replace(r'f\'Process_{getattr(document, \ document_id\, str(id(document)))}\'', 'f"Process_{getattr(document, \\\"document_id\\\", str(id(document)))}"')
content = content.replace(r'f\'Diagram_{getattr(document, \ document_id\, str(id(document)))}\'', 'f"Diagram_{getattr(document, \\\"document_id\\\", str(id(document)))}"')
content = content.replace(r'f\'Plane_{getattr(document, \ document_id\, str(id(document)))}\'', 'f"Plane_{getattr(document, \\\"document_id\\\", str(id(document)))}"')

# Write back
with open(r'c:\VCC\VPB\vpb\services\export_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed corrupted document_id references")
