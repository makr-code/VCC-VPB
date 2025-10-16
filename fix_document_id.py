import re

# Read file
with open(r'c:\VCC\VPB\vpb\services\export_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace document.document_id with safe accessor
content = re.sub(
    r'document\.document_id',
    'getattr(document, "document_id", str(id(document)))',
    content
)

# Write back
with open(r'c:\VCC\VPB\vpb\services\export_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Replaced all document.document_id references")
