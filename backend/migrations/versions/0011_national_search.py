"""Locale-independent Portuguese catalogue search; original text is unchanged."""
from alembic import op
revision='0011'
down_revision='0010'
branch_labels=None
depends_on=None

def upgrade():
    conn=op.get_bind().connection.driver_connection
    expression=conn.execute("SELECT pg_get_expr(d.adbin,d.adrelid) FROM pg_attrdef d JOIN pg_attribute a ON a.attrelid=d.adrelid AND a.attnum=d.adnum WHERE a.attrelid='national_catalogue_entry'::regclass AND a.attname='search_vector'").fetchone()[0]
    if 'translate' not in expression:
        conn.execute("""ALTER TABLE national_catalogue_entry ALTER COLUMN search_vector SET EXPRESSION AS
          (to_tsvector('portuguese',translate(lower(coalesce(name,'')||' '||coalesce(group_name,'')||' '||coalesce(class_name,'')||' '||coalesce(pdm_name,'')),
            'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑáàâãäéèêëíìîïóòôõöúùûüçñ',
            'aaaaaeeeeiiiiooooouuuucnaaaaaeeeeiiiiooooouuuucn')))""")

def downgrade():
    raise RuntimeError('A normalização da busca preserva originais; não remova evidências para reverter.')
