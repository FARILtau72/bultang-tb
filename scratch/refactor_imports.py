import os
import re

replacements = {
    r"from app.core.config import": "from app.core.config import",
    r"from app.core import config": "from app.core from app.core import config",
    r"from app.core.db import": "from app.core.db import",
    r"from app.core import db": "from app.core from app.core import db",
    r"from app.core.models import": "from app.core.models import",
    r"from app.core import models": "from app.core from app.core import models",
    r"from app.core.utils import": "from app.core.utils import",
    r"from app.core import utils": "from app.core from app.core import utils",
    r"from app.services.absensi_service import": "from app.services.absensi_service import",
    r"from app.services.auth_service import": "from app.services.auth_service import",
    r"from app.services.siswa_service import": "from app.services.siswa_service import",
    r"from app.services.token_service import": "from app.services.token_service import",
    r"from app.routes import": "from app.routes import",
    r"from routes\.": "from app.routes.",
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements.items():
        content = re.sub(old, new, content)
        
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

for root, _, files in os.walk('c:\\khusus project IT\\update_absensi_tb'):
    if 'venv' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))

print("Import replacement complete.")
