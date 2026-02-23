DOWNLOAD_PDF_SCRIPT = """
async () => {
    const downloadFile = (blob, fileName) => {
        const link = document.createElement('a');
        // create a blobURI pointing to our Blob
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        // some browser needs the anchor to be in the doc
        document.body.append(link);
        link.click();
        link.remove();
        // in case the Blob uses a lot of memory
        // setTimeout(() => URL.revokeObjectURL(link.href), 7000);
    };

    const response = await fetch(window.location.href);
    const blob = await response.blob();
    downloadFile(blob, 'file.pdf')
}
"""
