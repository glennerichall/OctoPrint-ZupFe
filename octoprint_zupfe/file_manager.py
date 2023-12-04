import datetime

from . import FileObject
from .utils import compute_md5


class Files:
    def __init__(self, api, file_manager, octo_id):
        self._file_manager = file_manager
        self._api = api
        self._octo_id = octo_id

    def path_on_disk(self, filename):
        if not filename.endswith('.gcode'):
            filename = filename + '.gcode'
        return self._file_manager.path_on_disk('local', filename)

    def save_file(self, filename, content):
        file_object = FileObject(content)
        original_filename = filename

        if not filename.endswith('.gcode'):
            filename = filename + '.gcode'

        self._file_manager.add_file('local', filename, file_object, allow_overwrite=True)

        if not original_filename == filename:
            self._file_manager.set_additional_metadata('local', filename,
                                                       'original_filename', original_filename)

    def get_file_info(self, filename):
        file_manager = self._file_manager
        file_path = file_manager.path_on_disk('local', filename)
        metadata = file_manager.get_metadata('local', file_path)

        if not 'md5_hash' in metadata:
            metadata["md5_hash"] = compute_md5(file_path)
            file_manager.set_metadata('local', file_path, metadata)

        if 'original_filename' in metadata:
            filename = metadata['original_filename']

        return {
            'filename': filename,
            'hash': metadata["md5_hash"]
        }

    async def list_files(self):
        # use REST api to fetch also last print date information, not available through file_manager
        response = await self._api.get("/files?recursive=true")
        response = await response.json()

        # flatten file list
        stack = response['files']
        files = []
        while len(stack) > 0:
            elem = stack.pop()
            if elem['type'] == 'machinecode':
                files.append(elem)
            elif elem['type'] == 'folder':
                for c in elem['children']:
                    stack.append(c)

        result = []
        file_manager = self._file_manager
        for file in files:
            metadata = file_manager.get_metadata('local', file['path'])

            if 'md5_hash' in metadata:
                md5_hash = metadata['md5_hash']
            else:
                file_path = file_manager.path_on_disk('local', file['path'])
                md5_hash = compute_md5(file_path)
                file_manager.set_additional_metadata('local', file['path'], 'md5_hash', md5_hash)

            filename = file['path']

            if 'original_filename' in metadata:
                filename = metadata['original_filename']

            last_print = None
            if 'prints' in file:
                last_print = file['prints']['last']['date']
                last_print = datetime.datetime.fromtimestamp(last_print).isoformat()
            obj = {
                'filename': filename,
                'size': file['size'],
                'name': file['name'],
                'hash': md5_hash,
                'creation': datetime.datetime.fromtimestamp(file['date']).isoformat(),
                'last_print': last_print,
                'printer_uuid': self._octo_id
            }
            result.append(obj)
        return result
