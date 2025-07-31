import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="aws-0-ap-southeast-1.pooler.supabase.com",
        port=5432,
        database="postgres",
        user="postgres.jxivdqlryyqlsccwcnxt",
        password="french4477"
    )
