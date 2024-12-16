

//#region Progress modal

// Register modal
const progress_modal = new bootstrap.Modal(document.querySelector('#progress_modal'), {
    keyboard: false
})

const progress_modal_text_element = document.querySelector('#progress_modal_text');

const progress_modal_spinner_element = document.querySelector('#progress_modal_spinner');

const progress_modal_ok_button_element = document.querySelector('#progress_modal_ok_button');

function progress_modal_ok_button_handler(event) {

    // Clear the modal's contents
    progress_modal_clear();
}
window.progress_modal_ok_button_handler = progress_modal_ok_button_handler;


progress_modal_ok_button_element.addEventListener('click', progress_modal_ok_button_handler);

function enable_progress_modal_ok_button_element() {

    progress_modal_spinner_element.style.display = 'none';

    progress_modal_ok_button_element.disabled = false;
}
window.enable_progress_modal_ok_button_element = enable_progress_modal_ok_button_element;


function disable_progress_modal_ok_button_element() {
    progress_modal_spinner_element.style.display = 'inline-block';
    progress_modal_ok_button_element.disabled = true;
}
window.disable_progress_modal_ok_button_element = disable_progress_modal_ok_button_element;

function progress_modal_show() {
    progress_modal.show();
}
window.progress_modal_show = progress_modal_show;

function progress_modal_hide() {

    progress_modal.hide();

    // Clear the modal's contents
    progress_modal_clear();
}
window.progress_modal_hide = progress_modal_hide;

/**
 * progress_modal_clear
 *
 * Clear content from the feedback modal.
 */
function progress_modal_clear() {

    // Clear any existing content in `progress_modal_text_element`
    Array.from(document.querySelector('#progress_modal_text').childNodes).forEach(node => node.remove());
}
window.progress_modal_clear = progress_modal_clear;

/**
 * progress_modal_update
 *
 * Append text content to the feedback modal.
 *
 * @param {string} text
 */
function progress_modal_update(text) {


    // Replace both backslashes and forward slashes with the
    // `Word Break Opportunity` tag followed by the slash..
    // this is to allow file paths to break at the slash

    text = text.replace(/[\\/]/g, "<wbr/>$&");

    if (text.startsWith("<wbr/>")){
        // remove <wbr/> if it is at the beginning of the string
        text = text.slice(6);
    }

    // If this is an error message...
    if (text.startsWith('ERROR:')) {

        // Add an appropriate class to the HTML
        text = `<p class="progress_error">${text}</p>`;

    }

    // If text is already wrapped in a tag...
    if (!text.trim().startsWith("<")) {

        // Append `text` to `progress_modal_text_element.innerHTML` wrapped in a <p />
        progress_modal_text_element.innerHTML += "<p>" + text + "</p>";

    } else {

        // Append `text` to `progress_modal_text_element.innerHTML`
        progress_modal_text_element.innerHTML += text;

    }
}
window.progress_modal_update = progress_modal_update;


//#endregion
