from db.base import Base

from models.users import User
from models.api_keys import APIKey
from models.audit_logs import AuditLogs


#for Alembic to detect the models when autogenerating migrations, and create relationships between them.