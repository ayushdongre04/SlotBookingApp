import uuid

from fastapi import Header

async def get_current_tenant_id(x_tenant_id: uuid.UUID = Header(...)) -> uuid.UUID:
    """
    Reads tenant_id from a header instead of a verified token. Need to change after auth.
    """
    return x_tenant_id
