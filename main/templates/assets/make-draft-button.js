function initPubDateButtons() {
    // check if form instantiation is to create new post or edit existing one
    var isCreateOp = {{ form.initial|yesno:"false,true" }};

    var pubDateElem = document.querySelector('input[name="published_at"]');
    if (pubDateElem.value === '') {

        // add 'set to today' functionality on publication date
        var setTodaySpan = document.getElementById('set-today');
        var setTodayAnchor = document.createElement('a');
        setTodayAnchor.innerText = 'set to today';
        setTodayAnchor.href='javascript:';
        setTodaySpan.appendChild(document.createTextNode(' — '));
        setTodaySpan.appendChild(setTodayAnchor);
        setTodaySpan.addEventListener('click', function () {
            var isoDate = new Date().toISOString().substring(0,10);
            document.querySelector('input[name="published_at"]').value = isoDate;
        });

    } else if (isCreateOp) {
        // add 'make draft / set to empty' functionality
        var setEmptySpan = document.getElementById('set-empty');
        var setEmptyAnchor = document.createElement('a');
        setEmptyAnchor.innerText = 'set as draft';
        setEmptyAnchor.href='javascript:';
        setEmptySpan.appendChild(document.createTextNode(' — '));
        setEmptySpan.appendChild(setEmptyAnchor);
        setEmptySpan.addEventListener('click', function () {
            document.querySelector('input[name="published_at"]').value = '';
        });
    }
}

// init
initPubDateButtons();
