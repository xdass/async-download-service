import os
import logging
import asyncio
import aiohttp
from asyncio.subprocess import create_subprocess_shell, PIPE
from aiohttp import web
import aiofiles

INTERVAL_SECS = 1

logger = logging.getLogger('download_server')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
logger.addHandler(ch)


def check_path():
    pass


async def archivate(request):
    archive_hash_idx = 2
    archive_hash = request.path.split('/')[archive_hash_idx]
    path_to_images = os.path.join(os.getcwd(), 'test_photos', archive_hash)

    if not os.path.exists(path_to_images):
        raise aiohttp.web.HTTPNotFound(text='Запрашиваемый архив не существует или был удален!')

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)

    process = await create_subprocess_shell(f'zip -j -r - {os.path.join(path_to_images, "*.*")}', stdout=PIPE, stderr=PIPE)

    while True:
        try:
            archive_chunk = await process.stdout.read(256)
            if archive_chunk:
                await asyncio.sleep(10)
                print(archive_chunk)
                logger.info(f'Sending archive chunk ...')
                await response.write(archive_chunk)
            else:
                return response
        except Exception as e:
            process.send_signal(9)
            raise
        finally:
            response.force_close()


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app, host='127.0.0.1')
