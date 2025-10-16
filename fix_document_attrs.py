import re

# Read file
with open(r'c:\VCC\VPB\vpb\services\export_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace document.elements with document.get_all_elements()
content = re.sub(r'\bdocument\.elements\b', 'document.get_all_elements()', content)

# Replace document.connections with document.get_all_connections()
content = re.sub(r'\bdocument\.connections\b', 'document.get_all_connections()', content)

# Fix metadata access patterns
content = re.sub(r'document\.title', 'document.metadata.title', content)
content = re.sub(r'document\.description', 'document.metadata.description', content)
content = re.sub(r'document\.author', 'document.metadata.author', content)

# Write back
with open(r'c:\VCC\VPB\vpb\services\export_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed document attribute access patterns")
print("   - document.elements → document.get_all_elements()")
print("   - document.connections → document.get_all_connections()")
print("   - document.title/description/author → document.metadata.*")
