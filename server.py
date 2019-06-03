import os
from functools import partial
import argparse
import logging
import asyncio
from asyncio.subprocess import create_subprocess_shell, create_subprocess_exec, PIPE
import aiohttp
from aiohttp import web
import aiofiles

logger = logging.getLogger('download_server')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
logger.addHandler(ch)


async def archivate(request, images_folder, use_delay):
    archive_hash = request.match_info['archive_hash']
    path_to_images = os.path.join(os.getcwd(), images_folder, archive_hash)

    if not os.path.exists(path_to_images):
        raise aiohttp.web.HTTPNotFound(text='Запрашиваемый архив не существует или был удален!')

    response = web.StreamResponse()
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    await response.prepare(request)

    all_images = os.path.join(path_to_images, "*.*")
    process = await create_subprocess_shell(f'zip -j -r - {all_images}', stdout=PIPE, stderr=PIPE)
    try:
        while True:
            archive_chunk = await process.stdout.read(256)
            if not archive_chunk:
                return response
            if use_delay:
                await asyncio.sleep(15)
            logger.info(f'Sending archive chunk ...')
            logger.debug(f'Debug')
            await response.write(archive_chunk)
    except asyncio.CancelledError:
        await create_subprocess_exec("./rkill.sh", f"{process.pid}")
        raise
    finally:
        response.force_close()


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def main(images_folder, use_delay):
    app = web.Application()
    partial_archivate = partial(archivate, images_folder=images_folder, use_delay=use_delay)
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', partial_archivate),
    ])
    web.run_app(app, host='127.0.0.1')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Microservice for download files')
    parser.add_argument('-d', '--debug', help="Print lots of debugging statements",
                        action="store_const",
                        dest="loglevel",
                        const=logging.DEBUG,
                        default=logging.DEBUG)
    parser.add_argument('-p', '--prod', help="Print info messages",
                        action="store_const",
                        dest="loglevel",
                        const=logging.INFO)
    parser.add_argument('--use_delay',
                        help='Enabled delay before send chunk(for debuging)',
                        type=bool,
                        default=False)
    parser.add_argument('images', metavar='i', help='Path to images folder')
    args = parser.parse_args()
    logger_level = args.loglevel
    use_delay = args.use_delay
    images_folder = args.images
    logger.setLevel(logger_level)
    main(images_folder, use_delay)
