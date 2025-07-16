


function init()
{
    var host_type = document.getElementById('host_type').innerHTML;

    var nwkId = document.getElementById("nwk_id").value;
    var token = document.getElementById("token").value;
    var canvas_id = getElmById("canvas_id").value;
    
    
    var wsUri;
    

    if (host_type == 'cpython') {
        if (window.location.protocol == 'https:'){
            wsUri = "wss://" + window.location.hostname + "/sockets/" + nwkId + "/ws?token=" + token + "|" + Date.now() + "&canvas_id=" + canvas_id;
        }
        else {
            wsUri = "ws://" + window.location.host + "/sockets/" + nwkId + "/ws?token=" + token + "|" + Date.now() + "&canvas_id=" + canvas_id;
          }
    }
    else if (host_type == 'esp32') {
        if (window.location.protocol == 'https:')
            wsUri = 'wss://' + window.location.hostname + '/wschat'
        else
            wsUri = 'ws://' + window.location.hostname + '/wschat';
    }
    console.log(wsUri);

    writeLineToChat("Connection to " + wsUri + "...")
    websocket           = new WebSocket(wsUri);
    websocket.onopen    = function(evt) { onOpen    (evt) };
    websocket.onclose   = function(evt) { onClose   (evt) };
    websocket.onmessage = function(evt) { onMessage (evt) };
    websocket.onerror   = function(evt) { onError   (evt) };
    getElmById("input-chat").addEventListener("keydown", onChatLine);
    getElmById("input-chat").addEventListener("keyup", clearChatLine);
    getElmById("input-chat").focus();
    this_history = [];
    this_history_idx = 0;
    iris.websocket = websocket;
    console.log(iris);
    document.getElementById('connect_button').style.visibility = 'hidden' 
}

function getElmById(id) {
    return document.getElementById(id);
}

function writeLineToChat(line)
{
    var elm = getElmById('chat');
    if (elm)
    {
        var lineElm = document.createElement('div');
        if (line) {
            var time = new Date().toLocaleTimeString();
            lineElm.innerText = "[" + time + "] " + line;
        }
        else
            lineElm.innerHTML = '&nbsp;';
        elm.appendChild(lineElm);
        elm.scrollTop = elm.scrollHeight;
    }
}


function onOpen(evt)
{
    writeLineToChat("[CONNECTED]")
    iris.websocket.send('get_webstuff');
}

function onClose(evt)
{
    writeLineToChat("[CONNECTION CLOSED]")
}

function onError(evt)
{
    writeLineToChat("[CONNECTION ERROR]")
}

function onMessage(evt)
{
    function parse(string) {
      const comma_index = string.indexOf(',');
      if (comma_index !== -1) {
          const pid = string.substring(0, comma_index);
          const data = string.substring(comma_index + 1);
          return { pid, data };
      } else {
          return null; // Comma not found in the string.
      }
    }
    
    //writeLineToChat(evt.data)
    console.log(evt.data);
    var msg = parse(evt.data)
    if (msg == null) {
      writeLineToChat('unknown event: ' + evt.data);
      return
    }
    
    if (msg.pid == 'term') {
      writeLineToChat(msg.data);
    }
    else if (msg.pid == 'compose_page') {
        iris.compose_page(msg.data)
    }

    else {
      console.log('pid: ' + msg.pid + ' data: ' + msg.data)
      iris.p[msg.pid](msg.pid, msg.data);
    }

}

function clearChatLine(e) {
    key = (e.key || e.keyCode);
    console.log(key);
    if ((key === 13 || key.toUpperCase() === "ENTER") && !event.shiftKey) {
        input = getElmById("input-chat");
        input.innerHTML = "";
    }
}

function onChatLine(e) {
    key = (e.key || e.keyCode);
    // console.log(key);
    var index = 0;
    
    if (key.toUpperCase() === "ARROWUP") {
        console.log(this_history[this_history_idx]);
        var chat = getElmById("input-chat")
        chat.focus(chat)
        chat.innerHTML = this_history[this_history_idx]
        this_history_idx += 1
        if (this_history_idx > this_history.length()){
            this_history_idx = this_history_idx;
        }
    }

    else if (key.toUpperCase() === "ARROWDOWN") {
        console.log(this_history[this_history_idx]);
        var chat = getElmById("input-chat")
        chat.focus(chat)
        chat.innerHTML = this_history[this_history_idx]
        this_history_idx -= 1
        if (this_history_idx < 0) {
            this_history_idx = 0;
        }
    }
    else if ((key === 13 || key.toUpperCase() === "ENTER") && !event.shiftKey) {
        input       = getElmById("input-chat");
        line        = input.innerHTML.trim();
        line = line.replace(/<br ?\/?>/g, "\n")
        line = line.replace(/&nbsp;/g, ' ')
        cleanText = line.replace(/<\/?[^>]+(>|$)/g, "");
        console.log(cleanText)
        this_history.unshift(line)
        // writeLineToChat(">>> " + cleanText)
        this_history_idx = 0
        input.innerHTML = "";

        if (line.length > 0)
            websocket.send(`term,${line}`);
    }
}


// window.addEventListener("load", init, false);




