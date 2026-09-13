import os
import sys

os.environ["SQLALCHEMY_URL"] = "postgresql://user:password@localhost:5432/svsp"

# Add backend to path
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from alembic.config import Config
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

# Load alembic config
config = Config(os.path.join(sys_path, "alembic.ini"))

# Override the sqlalchemy.url from env
config.set_main_option("sqlalchemy.url", os.environ["SQLALCHEMY_URL"])

# Import Base from our models
from core.database import Base

target_metadata = Base.metadata

# Run migration offline (generates SQL)
context = context.context  # This won't work either

# Let's use the standard approach
from alembic import script

# Use alembic command directly
import subprocess

result = subprocess.run(
    ["python", "-m", "alembic", "revision", "--autogenerate", "-m", "init schema"],
    capture_output=True,
    text=True,
    cwd=sys_path,
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
