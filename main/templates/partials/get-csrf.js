// get csrf token from django template variable
function getCsrf() {
    var inputElems = document.querySelectorAll('input');
    var csrfToken = '';
    var i = 0;
    for (i = 0; i < inputElems.length; i++) {
        if (inputElems[i].name === 'csrfmiddlewaretoken') {
            csrfToken = inputElems[i].value;
            break;
        }
    }
    return csrfToken;
}
