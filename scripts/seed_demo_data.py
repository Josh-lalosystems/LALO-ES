import sqlite3

def seed_agents():
    agents = [
        ('Demo Agent', 'demo'),
        ('Investor Pitch', 'pitch'),
        ('RAG Expert', 'rag'),
        ('Workflow Bot', 'workflow'),
        ('Support Agent', 'support'),
    ]
    conn = sqlite3.connect('lalo.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS agents (id INTEGER PRIMARY KEY, name TEXT, type TEXT)')
    cur.executemany('INSERT INTO agents (name, type) VALUES (?, ?)', agents)
    conn.commit()
    conn.close()

def seed_documents():
    docs = [
        ('Investor Pitch Deck', 'pitch.pdf'),
        ('RAG Sample Doc', 'rag.txt'),
        ('Workflow Example', 'workflow.md'),
    ]
    conn = sqlite3.connect('lalo.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, name TEXT, filename TEXT)')
    cur.executemany('INSERT INTO documents (name, filename) VALUES (?, ?)', docs)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("lalo.scripts.seed_demo_data")
    seed_agents()
    seed_documents()
    logger.info('Demo data seeded.')
