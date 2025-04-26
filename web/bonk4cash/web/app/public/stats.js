const chatlogbox = document.getElementById('chatlog')
const person = document.getElementById("username").innerText;

async function getChatLog(){
  const resp = await fetch("/transcript");
  if(resp.ok){
    const log = await resp.text();
    console.log(log);
    const filtered = log.split("\n").filter(msg => msg.split("]")[0].substring(1) === person).join("\n");
    chatlogbox.innerHTML = filtered;
  }else{
    chatlogbox.innerHTML = "<br />Failed to load messages"
  }
}

getChatLog()