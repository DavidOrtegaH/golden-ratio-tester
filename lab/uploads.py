"""Bounded memory-only uploads, including multipart requests without a size hint."""
from io import BytesIO
from django.core.exceptions import RequestDataTooBig
from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadedfile import InMemoryUploadedFile

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_BODY_BYTES = 11 * 1024 * 1024


class BoundedMemoryUploadHandler(FileUploadHandler):
    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        self.file = BytesIO()

    def receive_data_chunk(self, raw_data, start):
        if start + len(raw_data) > MAX_FILE_BYTES:
            self.file.close()
            raise RequestDataTooBig('Image upload exceeds the allowed size')
        self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        return InMemoryUploadedFile(self.file, self.field_name, self.file_name,
                                    self.content_type, file_size, self.charset,
                                    self.content_type_extra)

    def upload_interrupted(self):
        if hasattr(self, 'file'):
            self.file.close()
