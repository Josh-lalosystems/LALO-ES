from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('debug_test_app:app', host='127.0.0.1', port=9000, log_level='info')
