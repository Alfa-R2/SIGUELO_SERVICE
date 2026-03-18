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
INSERT_DIV_TO_SCREENSHOT_SCRIPT: str = """
() => {
    let rowsTable = document.getElementsByClassName('row');
    let rowsArray = Array.from(rowsTable);
    let rowsToUse = []
    for (let i = 3; i <= 10; i++) {
        rowsToUse.push(rowsArray[i])
    };
    let div = document.createElement('div');
    div.id = 'div-screenshot';
    let parent = rowsArray[3].parentNode;
    parent.insertBefore(div, rowsArray[3]);
    rowsToUse.forEach(row => {
        div.appendChild(row)
    });
    return div
}
"""
