from fastapi import FastAPI


app = FastAPI()


@app.get('/health')
async def health() -> dict:
    return {'status': 'ok'}


@app.get('/sum')
async def sum_endpoint(a: int, b: int) -> dict:
    return {'result': a + b}
