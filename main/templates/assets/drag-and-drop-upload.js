// setup for drag and drop uploading
document.getElementById('js-show').style.display = 'inline';
document.getElementById('js-status').style.color = '#f00';

// get body element, used for drag and drop onto it
var bodyElem = document.querySelector('textarea[name="body"]');

// prevent default drag and drop behaviours
[
    'drag',
    'dragstart',
    'dragend',
    'dragover',
    'dragenter',
    'dragleave',
    'drop',
].forEach(function (event) {
    bodyElem.addEventListener(event, function (e) {
        e.preventDefault();
        e.stopPropagation();
    });
});

function injectImageMarkdown(textInputElem, imageName, imageURL) {
    // build markdown image code
    var markdownImageCode = '![' + imageName + '](' + imageURL + ')';

    // inject markdown image code in cursor position
    if (textInputElem.selectionStart || textInputElem.selectionStart == '0') {
        var startPos = textInputElem.selectionStart;
        var endPos = textInputElem.selectionEnd;
        textInputElem.value = textInputElem.value.substring(0, startPos)
            + markdownImageCode
            + '\n'
            + textInputElem.value.substring(endPos, textInputElem.value.length);

        // set cursor location to after markdownImageCode +1 for the new line
        textInputElem.selectionEnd = endPos + markdownImageCode.length + 1;
    } else {
        // there is no cursor, just append
        textInputElem.value += markdownImageCode;
    }
}

bodyElem.addEventListener('drop', function (e) {
    // only upload one file at a time
    if (e.dataTransfer.files.length === 1) {

        // prepare form data
        var formData = new FormData();
        var name = e.dataTransfer.files[0].name;
        formData.append("file", e.dataTransfer.files[0]);

        // upload request
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function alertContents() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    // success, inject markdown snippet
                    injectImageMarkdown(bodyElem, name, xhr.responseURL);
                } else {
                    alert('Image could not be uploaded. ' + xhr.responseText);
                }

                // re-enable textarea
                bodyElem.disabled = false;

                // update status message
                document.getElementById('js-status').innerText = '';
            } else {
                // this branch runs first
                // uplading, so disable textarea and show status message
                bodyElem.disabled = true;
                document.getElementById('js-status').innerText = 'UPLOADING...';
            }
        };

        xhr.open('POST', '/images/?raw=true');
        xhr.setRequestHeader('X-CSRFToken', '{{ csrf_token }}');
        xhr.send(formData);
    }
});
