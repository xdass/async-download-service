import os
import argparse
import logging
import asyncio
from asyncio.subprocess import create_subprocess_shell, PIPE
import aiohttp
from aiohttp import web
import aiofiles

INTERVAL_SECS = 1

logger = logging.getLogger('download_server')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
logger.addHandler(ch)


async def archivate(request, use_delay):
    archive_hash_idx = 2
    archive_hash = request.path.split('/')[archive_hash_idx]
    path_to_images = os.path.join(os.getcwd(), 'test_photos', archive_hash)

    if not os.path.exists(path_to_images):
        raise aiohttp.web.HTTPNotFound(text='Запрашиваемый архив не существует или был удален!')

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)

    process = await create_subprocess_shell(f'zip -j -r - {os.path.join(path_to_images, "*.*")}', stdout=PIPE, stderr=PIPE)

    try:
        while True:
            archive_chunk = await process.stdout.read(256)
            if archive_chunk:
                if use_delay:
                    await asyncio.sleep(30)
                logger.info(f'Sending archive chunk ...')
                await response.write(archive_chunk)
            else:
                return response
    except asyncio.CancelledError:
        process.send_signal(19)
        raise
    finally:
        response.force_close()


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Microservice for download files')
    parser.add_argument('--logging', help='Enabled or Disabled logging(By default is Enabled)', type=bool, default=False)
    parser.add_argument('--use_delay', help='Enabled delay before send chunk(for debuging)', type=bool, default=False)
    parser.add_argument('images', metavar='i', help='Path to images folder')
    args = parser.parse_args()
    logger_state = args.logging
    use_delay = args.use_delay
    images_folder = args.images
    logger.disabled = logger_state
    full_path = os.path.join(images_folder, '{archive_hash}/')

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app, host='127.0.0.1')
