"""
Upload handlers to test the upload API.
"""

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.uploadhandler import (FileUploadHandler, StopUpload,
    StopFutureHandlers)
from StringIO import StringIO

class QuotaUploadHandler(FileUploadHandler):
    """
    This test upload handler terminates the connection if more than a quota
    (5MB) is uploaded.
    """
    
    QUOTA = 5 * 2**20 # 5 MB
    
    def __init__(self, request=None):
        super(QuotaUploadHandler, self).__init__(request)
        self.total_upload = 0
        
    def receive_data_chunk(self, raw_data, start):
        self.total_upload += len(raw_data)
        if self.total_upload >= self.QUOTA:
            raise StopUpload(connection_reset=True)
        return raw_data
            
    def file_complete(self, file_size):
        return None

class CustomUploadError(Exception):
    pass

class ErroringUploadHandler(FileUploadHandler):
    """A handler that raises an exception."""
    def receive_data_chunk(self, raw_data, start):
        raise CustomUploadError("Oops!")

class ContentTypeExtraUploadHandler(FileUploadHandler):
    """
    File upload handler that handles content_type_extra
    """

    def new_file(self, *args, **kwargs):
        super(ContentTypeExtraUploadHandler, self).new_file(*args, **kwargs)
        self.blobkey = self.content_type_extra.get('blob-key', '')
        self.file = StringIO()
        self.file.write(self.blobkey)
        self.active = self.blobkey is not None
        if self.active:
            raise StopFutureHandlers()

    def receive_data_chunk(self, raw_data, start):
        """
        Add the data to the StringIO file.
        """
        if not self.active:
            return raw_data

    def file_complete(self, file_size):
        if not self.active:
            return

        self.file.seek(0)
        return InMemoryUploadedFile(
            file = self.file,
            field_name = self.field_name,
            name = self.file_name,
            content_type = self.content_type,
            size = file_size,
            charset = self.charset
        )
