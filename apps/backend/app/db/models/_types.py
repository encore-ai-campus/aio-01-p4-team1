from datetime import datetime
from typing import Annotated

from sqlalchemy import BigInteger, DateTime, Identity, func
from sqlalchemy.orm import mapped_column

PrimaryKey = Annotated[int, mapped_column(BigInteger, Identity(), primary_key=True)]
CreatedAt = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]
