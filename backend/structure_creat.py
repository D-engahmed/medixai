import os
from pathlib import Path

# List of directories and files to create
structure = {
    "app": [
        "__init__.py", "main.py",
        {"config": ["__init__.py", "settings.py", "database.py"]},
        {"core": ["__init__.py", "security.py", "middleware.py", "dependencies.py"]},
        {"models": ["__init__.py", "user.py", "doctor.py", "appointment.py", "medication.py", "chat.py"]},
        {"schemas": ["__init__.py", "user.py", "auth.py", "doctor.py", "appointment.py", "medication.py"]},
        {"api": [
            "__init__.py",
            {"v1": ["__init__.py", "auth.py", "users.py", "doctors.py", "appointments.py", "medications.py", "chat.py", "dashboard.py"]}
        ]},
        {"services": ["__init__.py", "auth_service.py", "user_service.py", "doctor_service.py", "appointment_service.py", "medication_service.py", "chat_service.py", "geo_service.py", "payment_service.py", "notification_service.py"]},
        {"utils": ["__init__.py", "validators.py", "encryption.py", "logger.py", "helpers.py"]},
        {"tests": ["__init__.py", "conftest.py", "test_auth.py", "test_users.py", "test_appointments.py"]}
    ],
    "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.prod.yml", {"nginx": ["nginx.conf"]}],
    "k8s": ["namespace.yaml", "configmap.yaml", "secrets.yaml", "deployment.yaml", "service.yaml", "ingress.yaml"],
    "migrations": [{"alembic": []}],
    "docs": ["API.md", "SECURITY.md", "DEPLOYMENT.md"],
    ".env.example": None,
    ".gitignore": None,
    "README.md": None,
    "Makefile": None,
    "requirements.txt": None,
    "requirements-dev.txt": None
}

def create_structure(base_path: Path, struct: dict):
    for name, contents in struct.items():
        path = base_path / name
        if contents is None:
            # Create a file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
        elif isinstance(contents, list):
            # It's a directory
            path.mkdir(parents=True, exist_ok=True)
            # Recurse into directory contents
            for item in contents:
                if isinstance(item, str):
                    (path / item).touch(exist_ok=True)
                elif isinstance(item, dict):
                    create_structure(path, item)

if __name__ == "__main__":
    base = Path(".")
    create_structure(base, structure)
    print("Project structure created successfully.")
