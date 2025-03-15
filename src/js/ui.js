import Modal from 'bootstrap/js/dist/modal';

//#region Progress modal

// Register modal
const progress_modal = new Modal(document.querySelector('#progress_modal'), {
    keyboard: false
})
// temporarily expose the modal for debugging
window.progress_modal = progress_modal;

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

function splitOnSubstringAtStart(str, substring) {
    if (str.startsWith(substring)) {
        return [substring, str.substring(substring.length)];
    }
    return [str];
}




/**
 * progress_modal_update
 *
 * Append text content to the feedback modal.
 *
 * @param {string} text
 */
function progress_modal_update(text) {

    // show the modal if it is not already visible
    if (!progress_modal._isShown) {
        progress_modal.show();
    }

    // Replace both backslashes and forward slashes with the
    // `Word Break Opportunity` tag followed by the slash..
    // this is to allow file paths to break at the slash

    text = text.replace(/[\\/]/g, "<wbr/>$&");
    text = text.trim();

    if (text.startsWith("<wbr/>")){
        // remove <wbr/> if it is at the beginning of the string
        text = text.slice(6);
    }

    // If this is an error message...
    const error_split = splitOnSubstringAtStart(text, 'ERROR:');
    const warning_split = splitOnSubstringAtStart(text, 'WARNING:');

    if (error_split.length > 1) {
        // Add an appropriate class to the HTML
        text = `<p><span class="progress_error">${error_split[0]}</span>${error_split[1]}</p>`;
    } else if (warning_split.length > 1) {
        text = `<p><span class="progress_warning">${warning_split[0]}</span>${warning_split[1]}</p>`;
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

//#region Progress bar

class ProgressBar {
    static instances = {};

    constructor() {
        this.id = this.generateUniqueId();
        this.progress = 0;
        this.progress_bar = document.createElement('div');
        this.progress_bar.classList.add('progress','mb-3');
        this.progress_bar.setAttribute('role', 'progressbar');
        this.progress_bar.setAttribute('aria-valuenow', '0');
        this.progress_bar.setAttribute('aria-valuemin', '0');
        this.progress_bar.setAttribute('aria-valuemax', '100');
        this.progress_bar.setAttribute('area-label', 'progress bar');

        this.progress_bar_inner = document.createElement('div');
        this.progress_bar_inner.id = 'pb-inner';
        this.progress_bar_inner.classList.add('progress-bar', 'bg-primary');
        this.progress_bar_inner.style.width = '0%';

        this.progress_bar.appendChild(this.progress_bar_inner);

        if (!progress_modal._isShown){
            progress_modal.show();
        }
        progress_modal_text_element.appendChild(this.progress_bar);

        ProgressBar.instances[this.id] = this;
    }

    update(progress){
        this.progress = progress;
        this.progress_bar.setAttribute('aria-valuenow', progress);
        this.progress_bar_inner.style.width = `${progress}%`;
        this.progress_bar_inner.innerText = `${progress}%`;
    }

    reset(){
        this.progress = 0;
        this.progress_bar.setAttribute('aria-valuenow', '0');
        this.progress_bar_inner.style.width = '0%';
    }

    remove(){
        this.progress_bar.remove();
    }

    generateUniqueId() {
        return 'id-' + Date.now() + '-' + Math.floor(Math.random() * 10000);
      }
}
// progress_modal_text_element.appendChild(progress_bar);

window.newProgressBar = () => {
    console.log('newProgressBar called');
    const pb = new ProgressBar();
    console.log(pb.id);
    return pb.id;
}

window.updateProgressBar = (progress_bar_id, progress) => {
    console.log('updateProgressBar called with id:', progress_bar_id, 'and progress:', progress);
    console.log("type of id:", typeof progress_bar_id);
    console.log("type of progress:", typeof progress);
    if (ProgressBar.instances[progress_bar_id]){
        ProgressBar.instances[progress_bar_id].update(progress);
    }
    else{
        console.error('ProgressBar with id:', progress_bar_id, 'not found');
    }
}

// function add_bar_to_progress_modal(){
//     if (!progress_modal._isShown){
//         progress_modal.show();
//     }

//     progress_modal_text_element.appendChild(progress_bar);
// }

// function update_progress_bar(progress_bar, progress){
//     progress_bar.setAttribute('aria-valuenow', progress);
//     progress_bar.style.width = `${progress}%`;
// }

//#endregion
